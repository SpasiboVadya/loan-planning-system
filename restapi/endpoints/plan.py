"""Plan endpoints for the API."""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.init_db import get_db
from components.plan.repository import PlanRepository
from components.plan import schemas
from restapi.endpoints.auth import get_current_user
from components.user.models import User

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    responses={404: {"description": "Not found"}},
)

@router.get("/user_credits/{user_id}", response_model=List[schemas.UserCredit])
async def get_user_credits(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all credits for a specific user with their payment history."""
    repo = PlanRepository(db)
    credits = await repo.get_user_credits(user_id)
    
    if not credits:
        raise HTTPException(status_code=404, detail="No credits found for this user")
    
    return credits

@router.post("/insert")
async def insert_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Insert plans for the current month."""
    repo = PlanRepository(db)
    success = await repo.insert_plans()
    
    if success:
        return {"message": "Plans inserted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to insert plans")

@router.get("/performance", response_model=List[schemas.CategoryPerformance])
async def get_plans_performance(
    period: date = Query(..., description="Period to check (first day of the month)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance of plans for a specific period."""
    repo = PlanRepository(db)
    return await repo.get_plans_performance(period)

@router.get("/year-performance", response_model=schemas.YearPerformance)
async def get_year_performance(
    year: int = Query(..., description="Year to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get yearly performance analysis with total sums per plan category."""
    repo = PlanRepository(db)
    return await repo.get_year_performance(year) 