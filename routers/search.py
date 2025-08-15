from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Category
from schemas import UserResponse, CategoryOut
from dependencies import get_current_user  # ✅ Token validation

router = APIRouter(
    tags=["Search"],
    dependencies=[Depends(get_current_user)]  # ✅ All search routes require auth
)

# ✅ DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------- Search Categories --------
@router.get("/search/categories")
def search_categories(
    q: str = Query(..., description="Search term for category name"),
    db: Session = Depends(get_db)
):
    results = db.query(Category).filter(Category.name.ilike(f"%{q}%")).all()
    return {
        "IsSuccess": True,
        "message": f"Found {len(results)} categories" if results else "No categories found",
        "data": results
    }

# -------- Search Users --------
@router.get("/search/users")
def search_users(
    q: str = Query(..., description="Search term for user name or email"),
    db: Session = Depends(get_db)
):
    results = db.query(User).filter(
        (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).all()
    return {
        "IsSuccess": True,
        "message": f"Found {len(results)} users" if results else "No users found",
        "data": results
    }

# -------- Search Both --------
@router.get("/search/all")
def search_all(
    q: str = Query(..., description="Search term for categories and users"),
    db: Session = Depends(get_db)
):
    categories = db.query(Category).filter(Category.name.ilike(f"%{q}%")).all()
    users = db.query(User).filter(
        (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).all()
    return {
        "IsSuccess": True,
        "message": "Search completed",
        "categories": categories,
        "users": users
    }
