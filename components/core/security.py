"""Security utilities for JWT and password handling."""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import os
from jose import JWTError, jwt
from components.core.config import get_settings

settings = get_settings()

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    salt, stored_hash = hashed_password.split(':')
    return get_password_hash(plain_password, salt) == hashed_password

def get_password_hash(password: str, salt: str = None) -> str:
    """Generate password hash using SHA256 with salt."""
    if salt is None:
        salt = os.urandom(32).hex()
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode())
    hash_obj.update(password.encode())
    return f"{salt}:{hash_obj.hexdigest()}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None 