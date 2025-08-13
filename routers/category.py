from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Category, User
from database import get_db
from schemas import CategoryOut, UserLocation
from dependencies import get_current_user  # token validation
import math

router = APIRouter(tags=["Category"])

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
    
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# -------- Get All Categories --------
@router.get("/category", response_model=list[CategoryOut])
def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)
    return db.query(Category).all()

# -------- Get Category by ID or Name --------
@router.get("/category/{identifier}", response_model=CategoryOut)
def get_category(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_verified_user(current_user)

    # Try ID lookup first
    category = None
    if identifier.isdigit():
        category = db.query(Category).filter(Category.id == int(identifier)).first()
    else:
        category = db.query(Category).filter(Category.name.ilike(identifier)).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category

 # ✅ 3. post category with category AND LIST OF it
@router.post("/category/nearest")
def assign_nearest_category(
    location: UserLocation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).all()
    if not categories:
        raise HTTPException(status_code=404, detail={"IsSuccess": False, "message": "No categories found"})

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

