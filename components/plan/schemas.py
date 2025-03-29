"""Pydantic schemas for user data validation."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    login: str


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str


class UserUpdate(BaseModel):
    """Schema for user updates."""
    login: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """Schema for user in database."""
    id: int
    registration_date: date

    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema for user response."""
    pass


class UserWithToken(User):
    """Schema for user with JWT token."""
    access_token: str
    token_type: str = "bearer"
