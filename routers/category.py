from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Category, User
from database import get_db
from schemas import CategoryOut, UserLocation
from dependencies import get_current_user  # ✅ Token validation
import math

router = APIRouter(
    tags=["Category"],
    dependencies=[Depends(get_current_user)]  # ✅ Enforce authentication for all routes
)

# ✅ DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Haversine formula for distance calculation
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# -------- Get All Categories --------
@router.get("/category")
def get_all_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return {
        "IsSuccess": True,
        "message": "Categories retrieved successfully" if categories else "No categories found",
        "data": categories
    }

# -------- Get Category by ID or Name --------
@router.get("/category/{identifier}")
def get_category(identifier: str, db: Session = Depends(get_db)):
    if identifier.isdigit():
        category = db.query(Category).filter(Category.id == int(identifier)).first()
    else:
        category = db.query(Category).filter(Category.name.ilike(identifier)).first()

    if not category:
        return {"IsSuccess": False, "message": "Category not found"}

    return {"IsSuccess": True, "message": "Category retrieved successfully", "data": category}

# -------- Post: Find Nearest Category --------
@router.post("/category/nearest")
def assign_nearest_category(location: UserLocation, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    if not categories:
        return {"IsSuccess": False, "message": "No categories found"}

    nearby = []
    for cat in categories:
        if cat.latitude is None or cat.longitude is None:
            continue
        dist = haversine(location.latitude, location.longitude, cat.latitude, cat.longitude)
        if location.radius_km is None or dist <= location.radius_km:
            nearby.append({
                "id": cat.id,
                "category": cat.name,
                "image": cat.image,
                "latitude": cat.latitude,
                "longitude": cat.longitude,
                "distance_km": round(dist, 2)
            })

    if not nearby:
        return {"IsSuccess": False, "message": "No categories found within radius"}

    nearest = sorted(nearby, key=lambda x: x["distance_km"])[0]
    return {
        "IsSuccess": True,
        "message": f"Nearest category '{nearest['category']}' assigned",
        "data": nearest,
        "list": nearby
    }
