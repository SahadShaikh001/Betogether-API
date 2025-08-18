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
    register_type: str = Form(...), # manual or google_auth
    uid: str = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Email validation
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return {"IsSucces": False, "message":str(e)}

    if register_type not in ["manual", "google_auth"]:
        return {"IsSucces": False, "message": "Invalid register_type."}

    if register_type == "manual" and not password:
        return  {"IsSucces": False, "message": "Password required for manual login."}

    if db.query(User).filter(User.email == email).first():
        return {"IsSucces": False, "message": "Email already registered."}

    hashed_password = None
    if register_type == "manual":
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
    if register_type == "manual":
        otp_code, otp_expiry = generate_otp()  # ✅ get OTP from util
        new_user.otp_code = otp_code
        new_user.otp_expiry = otp_expiry
        send_otp_email(email, otp_code)
    else:
        new_user.otp_verified = True

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"IsSucces": True, "message": "OTP sent. Please verify." if register_type == "manual" else "Registered successfully."}
# ------------------ VERIFY OTP registration------------------
@router.post("/verify-otp-reg")
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return{"IsSucces": False, "message":"User not found"}

    if not user.otp_code or not user.otp_expiry:
        return{"IsSucces": False, "message":"No OTP generated"}

    if datetime.utcnow() > user.otp_expiry:
        return{"IsSucces": False, "message":"OTP expired"}

    if user.otp_code != payload.otp:
        return{"IsSucces": False,"message":"Invalid OTP"}

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
        "message": "Registration Successfully.",
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
            "otp_verified": user.otp_verified
        }
    }
# ------------------ LOGIN ------------------
@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        return {"IsSucces": False, "message": "User not found,check email & password."}

    if user_data.login_type == "manual":
        if not user.hashed_password or not user_data.password:
            return {"IsSucces": False, "message": "User not found,check email & Password ."}
        if not pwd_context.verify(user_data.password, user.hashed_password):
            return {"IsSucces": False, "message": "User not found,check email & password."}

        otp_code, otp_expiry = generate_otp()
        user.otp_code = otp_code
        user.otp_expiry = otp_expiry
        user.otp_verified = False
        db.commit()
        send_otp_email(user.email, otp_code)
        return {"IsSucces": True, "message": "OTP sent for login. Please verify.", "require_otp": True}

    if user_data.login_type == "google_auth":
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
                "login_type": user.login_type,
                "otp_verified": user.otp_verified,
            }
        }

# ------------------ VERIFY OTP login------------------
@router.post("/verify-otp-login")
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return{"IsSucces": False, "message":"User not found"}

    if not user.otp_code or not user.otp_expiry:
        return{"IsSucces": False, "message":"No OTP generated"}

    if datetime.utcnow() > user.otp_expiry:
        return{"IsSucces": False, "message":"OTP expired"}

    if user.otp_code != payload.otp:
        return{"IsSucces": False,"message":"Invalid OTP"}

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
        "message": "Login Successfully.",
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
            "login_type":user.login_type,
            "otp_verified": user.otp_verified
        }
    }
# ------------------ RESET OTP ------------------
@router.post("/reset-otp")
def reset_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return{"IsSucces": False, "message":"User not found"}

    if user.register_type != "manual":
        return{"IsSucces": False, "message":"OTP not required for social login"}

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
        return{"IsSucces": False, "message":"Invalid refresh token."}
    email = decoded.get("sub")
    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}

