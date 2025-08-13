from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database import SessionLocal
from models import User
from schemas import UserResponse, UserProfileResponse
from dependencies import get_current_user

router = APIRouter(tags=["Users"])

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

# -------- Get All Users --------
@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)
    return db.query(User).all()

# -------- Get User By ID --------
@router.get("users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
