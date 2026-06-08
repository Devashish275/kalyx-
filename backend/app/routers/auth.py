import os
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
import jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models import User

# Load config
JWT_SECRET = os.getenv("JWT_SECRET", "hackathon_super_secret_key_kalyx_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
from app.security import limit_signup, limit_login

# Pydantic schemas
class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLoginSchema(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Password hashing utilities
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Token utility
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        token = request.query_params.get("token")
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(func.lower(User.email) == func.lower(email.strip())).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/signup", response_model=TokenResponse, dependencies=[Depends(limit_signup)])
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    username_clean = payload.username.strip().lower()

    # Check if user already exists (by email)
    existing_email = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email is already registered")
        
    # Check if username already taken
    existing_username = db.query(User).filter(func.lower(User.username) == username_clean).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username is already taken")
        
    hashed = hash_password(payload.password)
    user = User(
        email=email_clean,
        username=username_clean,
        hashed_password=hashed,
        full_name=payload.full_name.strip() if payload.full_name else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "email": user.email, 
            "username": user.username,
            "full_name": user.full_name
        }
    }

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_login)])
def login(payload: UserLoginSchema, db: Session = Depends(get_db)):
    login_str = payload.username_or_email.strip()
    user = db.query(User).filter(
        (func.lower(User.email) == func.lower(login_str)) | 
        (func.lower(User.username) == func.lower(login_str))
    ).first()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
        
    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "email": user.email, 
            "username": user.username,
            "full_name": user.full_name
        }
    }
