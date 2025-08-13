from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from utils.jwt_handler import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from database import get_db
from models import User

# OAuth2 scheme setup – points to login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Token data model
class TokenData(BaseModel):
    sub: str | None = None

# Get the current user from the token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Decode JWT token, validate expiry, and extract the current user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

        # Fetch user from DB
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception