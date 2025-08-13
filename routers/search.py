from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from database import get_db
from models import User, Category
from schemas import UserResponse, CategoryOut
from dependencies import get_current_user

router = APIRouter(tags=["Search"])

# Dependency to get DB session
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
            status_code=403,
            detail="Please verify your OTP before accessing this feature."
        )

# -------- Search Categories --------
@router.get("/search/categories", response_model=list[CategoryOut])
def search_categories(
    q: str = Query(..., description="Search term for category name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)
    return db.query(Category).filter(Category.name.ilike(f"%{q}%")).all()

# -------- Search Users --------
@router.get("/search/users", response_model=list[UserResponse])
def search_users(
    q: str = Query(..., description="Search term for user name or email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)
    return db.query(User).filter(
        (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).all()

# -------- Search Both --------
@router.get("/search/all")
def search_all(
    q: str = Query(..., description="Search term for categories and users"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)
    categories = db.query(Category).filter(Category.name.ilike(f"%{q}%")).all()
    users = db.query(User).filter(
        (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).all()
    return {
        "categories": categories,
        "users": users
    }
