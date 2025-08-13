from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import auth, users, category, search, profile
from database import SessionLocal, engine
from models import Category, Base
from contextlib import asynccontextmanager

def seed_default_categories():
    db = SessionLocal()

    default_categories = [
        {"name": "Sports", "image": "/static/icons/sports.png", "latitude": 40.7128, "longitude": -74.0060},
        {"name": "find a ride", "image": "/static/icons/ride.png", "latitude": 34.0522, "longitude": -118.2437},
        {"name": "attend show", "image": "/static/icons/show.png", "latitude": 51.5074, "longitude": -0.1278},
        {"name": "join a event", "image": "/static/icons/event.png", "latitude": 35.6895, "longitude": 139.6917},
        {"name": "explore area", "image": "/static/icons/explore.png", "latitude": 48.8566, "longitude": 2.3522},
        {"name": "keep company", "image": "/static/icons/company.png", "latitude": 37.7749, "longitude": -122.4194},
        {"name": "translator", "image": "/static/icons/translator.png", "latitude": 55.7558, "longitude": 37.6173},
        {"name": "transport", "image": "/static/icons/transport.png", "latitude": -33.8688, "longitude": 151.2093},
        {"name": "cooking", "image": "/static/icons/cooking.png", "latitude": 52.5200, "longitude": 13.4050},
        {"name": "plumber", "image": "/static/icons/plumber.png", "latitude": 41.9028, "longitude": 12.4964},
    ]

    for cat in default_categories:
        existing = db.query(Category).filter_by(name=cat["name"]).first()
        if not existing:
            db.add(Category(
                name=cat["name"],
                image=cat["image"],
                latitude=cat["latitude"],
                longitude=cat["longitude"]
            ))

    db.commit()
    db.close()
    print("✅ Default categories with locations seeded")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Ensure tables exist first
    Base.metadata.create_all(bind=engine)
    seed_default_categories()
    yield
    # Shutdown code (if any)

app = FastAPI(title="BETOGETHER API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(category.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(profile.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "BETOGETHER API is running"}