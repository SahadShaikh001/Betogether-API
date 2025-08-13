from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
import shutil, os, uuid, json, random
from schemas import UserCreate, UserLogin, OTPRequest, OTPVerifyRequest, TokenRefreshRequest
from passlib.context import CryptContext
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from database import get_db
from utils.email_utils import send_otp_email
from utils.otp_utils import generate_otp
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

router = APIRouter(tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "static/profile_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ REGISTER ------------------
@router.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    password: str = Form(None),
    register_type: str = Form(...),
    uid: str = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Email validation
    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if register_type not in ["manual_login", "social_login"]:
        raise HTTPException(status_code=400, detail="Invalid register_type.")

    if register_type == "manual_login" and not password:
        raise HTTPException(status_code=400, detail="Password required for manual login.")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_password = None
    if register_type == "manual_login":
        hashed_password = pwd_context.hash(password)

    image_path = None
    if profile_image:
        ext = profile_image.filename.split(".")[-1]
        image_name = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(UPLOAD_DIR, image_name)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(profile_image.file, buffer)

    new_user = User(
        uid=uid,
        name=name,
        email=email,
        mobile=mobile,
        hashed_password=hashed_password,
        profile_image=image_path,
        register_type=register_type
    )
    if register_type == "manual_login":
        otp_code, otp_expiry = generate_otp()  # ✅ get OTP from util
        new_user.otp_code = otp_code
        new_user.otp_expiry = otp_expiry
        send_otp_email(email, otp_code)
    else:
        new_user.otp_verified = True

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"IsSucces": True, "message": "OTP sent. Please verify." if register_type == "manual_login" else "Registered successfully."}

# ------------------ LOGIN ------------------
@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        return {"IsSucces": False, "message": "Invalid credentials."}

    if user_data.register_type == "manual_login":
        if not user.hashed_password or not user_data.password:
            return {"IsSucces": False, "message": "Password required."}
        if not pwd_context.verify(user_data.password, user.hashed_password):
            return {"IsSucces": False, "message": "Invalid credentials."}

        otp_code, otp_expiry = generate_otp()
        user.otp_code = otp_code
        user.otp_expiry = otp_expiry
        user.otp_verified = False
        db.commit()
        send_otp_email(user.email, otp_code)
        return {"IsSucces": True, "message": "OTP sent for login. Please verify.", "require_otp": True}

    if user_data.register_type == "social_login":
        if user_data.uid:
            user.uid = user_data.uid
        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})
        user.access_token = access_token
        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)
        return {
            "IsSucces": True,
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "uid": user.uid,
                "name": user.name,
                "email": user.email,
                "mobile": user.mobile,
                "profile_image": user.profile_image,
                "register_type": user.register_type,
                "otp_verified": user.otp_verified,
            }
        }

# ------------------ VERIFY OTP ------------------
@router.post("/verify-otp")
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.otp_code or not user.otp_expiry:
        raise HTTPException(status_code=400, detail="No OTP generated")

    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user.otp_code != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user.otp_verified = True
    user.otp_code = None
    user.otp_expiry = None
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    user.access_token = access_token
    user.refresh_token = refresh_token
    db.commit()
    db.refresh(user)

    return {
        "IsSucces": True,
        "message": "Success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "uid": user.uid,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "profile_image": user.profile_image,
            "register_type": user.register_type,
            "otp_verified": user.otp_verified,
        }
    }

# ------------------ RESET OTP ------------------
@router.post("/reset-otp")
def reset_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.register_type != "manual_login":
        raise HTTPException(status_code=400, detail="OTP not required for social login")

    otp_code, otp_expiry = generate_otp()
    user.otp_code = otp_code
    user.otp_expiry = otp_expiry
    user.otp_verified = False
    db.commit()
    send_otp_email(user.email, otp_code)

    return {"IsSucces": True, "message": "New OTP sent successfully."}

# ------------------ REFRESH TOKEN ------------------
@router.post("/refresh-token")
def refresh_token(payload: TokenRefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    email = decoded.get("sub")
    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}
