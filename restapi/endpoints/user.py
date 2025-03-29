"""User endpoints for the API."""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.init_db import get_db
from components.user.repository import UserRepository
from components.user import schemas
from restapi.endpoints.auth import get_current_user
from components.user.models import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    repo = UserRepository(db)
    
    # Check if user with this login already exists
    if await repo.exists(user.login):
        raise HTTPException(
            status_code=400,
            detail="User with this login already exists"
        )
    
    return await repo.create(user)


@router.get("/", response_model=List[schemas.User])
async def read_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
    registration_date_from: date | None = Query(None, description="Filter users registered after this date"),
    registration_date_to: date | None = Query(None, description="Filter users registered before this date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users with optional filtering."""
    repo = UserRepository(db)
    return await repo.get_all(
        skip=skip,
        limit=limit,
        registration_date_from=registration_date_from,
        registration_date_to=registration_date_to
    )


@router.get("/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/by-login/{login}", response_model=schemas.User)
async def read_user_by_login(
    login: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by login."""
    repo = UserRepository(db)
    user = await repo.get_by_login(login)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user."""
    repo = UserRepository(db)
    
    # Check if user exists
    if not await repo.get_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if new login is already taken by another user
    existing_user = await repo.get_by_login(user.login)
    if existing_user and existing_user.id != user_id:
        raise HTTPException(
            status_code=400,
            detail="Login is already taken by another user"
        )
    
    updated_user = await repo.update(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user."""
    repo = UserRepository(db)
    if not await repo.delete(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.get("/with-credits/", response_model=List[schemas.User])
async def get_users_with_credits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users who have credits."""
    repo = UserRepository(db)
    return await repo.get_users_with_credits()