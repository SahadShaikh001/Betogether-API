from sqlalchemy import Column, Integer, String, Table, ForeignKey, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# Association table for many-to-many relationship between User and Interest
user_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"))
)

# Association table for user languages (many-to-many)
user_languages = Table(
    "user_languages",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("language_id", Integer, ForeignKey("languages.id")),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, nullable=True)  # ✅ Google UID (optional)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for Google signup
    profile_image = Column(String, nullable=True)
    register_type = Column(String, nullable=False, default="manual")  # manual or google_auth
    login_type = Column(String, nullable=False, default="manual")  # manual or google_auth
    otp_code = Column(String(4), nullable=True)  # 4-digit OTP
    otp_expiry = Column(DateTime, nullable=True)  # OTP expiry
    otp_verified = Column(Boolean, default=False)
    is_google_auth = Column(Boolean, default=False)  # True if registered via Google
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Many-to-many relationship with interests
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    # Many-to-many with Language only
    languages = relationship("Language", secondary=user_languages, back_populates="users", lazy="joined")

    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Removed users relationship, since user interests removed

class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Back reference to users
    users = relationship("User", secondary=user_interests, back_populates="interests")

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    users = relationship("User", secondary=user_languages, back_populates="languages")
