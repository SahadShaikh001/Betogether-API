from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union
from datetime import datetime

# ---------- Registration ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str
    profile_image: Optional[str] = None
    register_type: str  # manual / google_auth
    uid: Optional[str] = None  # Google UID (optional)

# ---------- Login ----------
class UserLogin(BaseModel):
    email: EmailStr
    password: Optional[str] = None  # Optional for social login
    login_type: str # manual/google_auth 
    uid:Optional[str] = None #google uid (optional)


# ---------- OTP Verification ----------
class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


# ---------- Tokens ----------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------- Category ----------
class CategoryOut(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    latitude: float
    longitude: float
    
    class Config:
        from_attributes = True


class CategoryIDName(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# ---------- Language ----------
class LanguageOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ---------- Profile Update ----------
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    languages: Optional[List[int]] = None  # language IDs only
    interests: Optional[List[int]] = None  # category IDs only


# ---------- Profile Response ----------
class UserProfileResponse(BaseModel):
    id: int
    uid:Optional[str]
    name: str
    email: EmailStr
    mobile: str
    profile_image: Optional[str]
    bio: Optional[str]
    languages: List[LanguageOut] = []
    interests: List[CategoryOut] = []
    otp_verified_verified: bool

    class Config:
        from_attributes = True


# ---------- Minimal User Response ----------
class UserResponse(BaseModel):
    id: int
    uid: Optional[str] = None
    name: str
    email: EmailStr
    mobile: str
    profile_image: Optional[str] = None
    register_type: Optional[str] = None
    otp_verified: bool

    class Config:
        from_attributes = True


# ---------- Auth Response ----------
class AuthResponse(BaseModel):
    IsSucces: bool
    message: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_type: str = "bearer"
    user: Optional[Union[UserResponse, UserProfileResponse]]


# ---------- Base Response ----------
class BaseResponse(BaseModel):
    IsSucces: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ---------- Token Refresh ----------
class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ---------- User Location ----------
class UserLocation(BaseModel):
    latitude: float
    longitude: float

    radius_km: Optional[float] = None  # optional filtering
