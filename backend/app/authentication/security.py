from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database.session import get_db
from app.database.models import User
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def hash_password(password: str) -> str: return pwd_context.hash(password)
def verify_password(password: str, hashed: str) -> bool: return pwd_context.verify(password, hashed)
def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.secret_key, algorithm=settings.algorithm)
def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    try: user_id = int(jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])["sub"])
    except (JWTError, ValueError, KeyError): raise error
    user = db.get(User, user_id)
    if not user or not user.active: raise error
    return user
def require_roles(*roles):
    def dependency(user: User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, "Insufficient permissions")
        return user
    return dependency
