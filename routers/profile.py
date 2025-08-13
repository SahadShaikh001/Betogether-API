from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database import SessionLocal
from models import User, Category, Language
from schemas import UserProfileUpdate, UserProfileResponse, BaseResponse
from dependencies import get_current_user

router = APIRouter(tags=["Profile"])

# ✅ DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# ✅ Helper for OTP check
def ensure_verified_user(user: User):
    if user.register_type == "manual_login" and not user.otp_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your OTP before accessing this feature."
        )

# -------- Get Current User Profile --------
@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    ensure_verified_user(current_user)
    return current_user

# -------- Update Profile --------
@router.put("/update-profile", response_model=BaseResponse)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)

    if payload.name:
        current_user.name = payload.name
    if payload.bio:
        current_user.bio = payload.bio
    if payload.profile_image:
        current_user.profile_image = payload.profile_image

    # Update Languages
    if payload.languages is not None:
        current_user.languages.clear()
        langs = db.query(Language).filter(Language.id.in_(payload.languages)).all()
        current_user.languages.extend(langs)

    # Update Interests
    if payload.interests is not None:
        current_user.interests.clear()
        cats = db.query(Category).filter(Category.id.in_(payload.interests)).all()
        current_user.interests.extend(cats)

    db.commit()
    db.refresh(current_user)

    return BaseResponse(IsSucces=True, message="Profile updated successfully.")
