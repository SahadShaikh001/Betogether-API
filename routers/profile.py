from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
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

# -------- Get Current User Profile --------
@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "IsSuccess": True,
        "message": "Profile retrieved successfully",
        "data": current_user
    }

# -------- Update Profile --------
@router.put("/update-profile")
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    return {
        "IsSuccess": True,
        "message": "Profile updated successfully"
    }
