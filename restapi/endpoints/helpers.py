"""Helper endpoints for work with users."""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.init_db import get_db
from components.user.repository import UserRepository
from components.user import schemas
from components.plan import schemas as plan_schemas
from restapi.endpoints.auth import get_current_user
from components.user.models import User

router = APIRouter(
    prefix="/helpers",
    tags=["helpers"],
    responses={404: {"description": "Not found"}},
)
@router.get("/users-with-credits/", response_model=List[schemas.User])
async def get_users_with_credits(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get all users who have credits."""
    repo = UserRepository(db)
    return await repo.get_users_with_credits()


@router.get("/users-with-open-loans/", response_model=List[plan_schemas.UserWithOpenLoans])
async def get_users_with_open_loans(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get all users who have open loans.

    Returns a list of users with their open loan information including:
    - User ID, login, and registration date
    - List of open loans for each user with loan details
    """
    repo = UserRepository(db)
    users = await repo.get_users_with_open_loans()

    if not users:
        raise HTTPException(status_code=404, detail="No users with open loans found")

    return users