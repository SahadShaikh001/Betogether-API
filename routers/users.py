from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import User
from dependencies import get_current_user

router = APIRouter(
    tags=["Users"],
    dependencies=[Depends(get_current_user)]  # ✅ Enforce authentication for all routes in this router
)

# ✅ DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------- Get All Users --------
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {
        "isSuccess": True,
        "message": "User list retrieved successfully",
        "data": users
    }

# -------- Get User By ID --------
@router.get("/users/{id}")
def get_user_by_id(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return {
            "isSuccess": False,
            "message": "User not found",
            "data": None
        }
    return {
        "isSuccess": True,
        "message": "User fetched successfully",
        "data": user
    }
