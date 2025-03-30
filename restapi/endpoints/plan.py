"""Plan endpoints for the API."""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import io

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
    """
    Get all credits for a specific user with loan information.
    
    Returns:
    - Date the loan was issued
    - Boolean whether the loan is closed (true - closed, false - open)
    
    For closed loans:
    - Date of loan repayment
    - Loan amount disbursed
    - Accrued interest
    - Amount of payments on the loan
    
    For open loans:
    - Loan repayment deadline
    - Number of days the loan is overdue
    - The amount of the loan
    - Accrued interest
    - The amount of payments on the body
    - Amount of interest payments
    """
    repo = PlanRepository(db)
    credits = await repo.get_user_credits(user_id)
    
    if not credits:
        raise HTTPException(status_code=404, detail="No credits found for this user")
    
    return credits

@router.post("/insert", response_model=schemas.PlanUploadResponse)
async def upload_plans(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload plans for a new month from a CSV file.
    
    The CSV file must have the following columns:
    - period: First day of the month in DD.MM.YYYY format (e.g., 01.01.2023)
    - sum: The plan amount (cannot be empty, can be 0)
    - category_id: The ID of the category
    
    Validations:
    - Period must be the first day of a month
    - Category ID must exist in the dictionary
    - Sum cannot be empty (0 is valid)
    - Plan must not already exist for the month and category
    """
    # Check if file is CSV
    if not file.filename.endswith('.csv'):
        return schemas.PlanUploadResponse(
            success=False, 
            message="Invalid file format. Only CSV files (.csv) are supported."
        )
    
    repo = PlanRepository(db)
    
    # Process the file
    file_content = await file.read()
    success, message, errors = await repo.upload_plans_from_csv(io.BytesIO(file_content))
    
    if not success:
        error_objects = [schemas.PlanUploadError(**error) for error in errors]
        return schemas.PlanUploadResponse(
            success=False,
            message=message,
            errors=error_objects
        )
    
    return schemas.PlanUploadResponse(
        success=True,
        message=message
    )

@router.get("/performance", response_model=List[schemas.CategoryPerformance])
async def get_plans_performance(
    as_of_date: date = Query(..., description="Date as of which to check plan execution"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance of plans as of a specific date.
    
    Returns:
    - Month of the plan
    - Plan category
    - Amount from the plan
    - Amount of credits issued (for plans with the "Issue" category) or payments collected (for "Collect" category)
    - % of plan fulfillment
    
    All calculations are based on data from the beginning of the plan month to the specified date (inclusive).
    """
    repo = PlanRepository(db)
    return await repo.get_plans_performance(as_of_date)

@router.get("/year-performance", response_model=schemas.YearPerformance)
async def get_year_performance(
    year: int = Query(..., description="Year to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get yearly performance analysis with total sums per plan category."""
    repo = PlanRepository(db)
    return await repo.get_year_performance(year)

@router.get("/year-summary", response_model=schemas.YearSummary)
async def get_year_summary(
    year: int = Query(..., description="Year to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summarized monthly information for a given year.
    
    Returns monthly summaries with:
    - Month and year
    - Number of issues (credits) for the month
    - Amount from the plan for the month
    - Total amount of payments for the month
    - % fulfillment of the plan for payments
    - Number of payments per month
    - Amount from the collection plan for the month
    - Amount of payments for the month
    - % fulfillment of the collection plan
    - % of the amount of issues for the month from the amount of issues for the year
    - % of the amount of payments for the month from the amount of payments for the year
    """
    repo = PlanRepository(db)
    return await repo.get_year_summary(year)

@router.get("/users-with-open-loans", response_model=List[schemas.UserWithOpenLoans])
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
    repo = PlanRepository(db)
    users = await repo.get_users_with_open_loans()
    
    if not users:
        raise HTTPException(status_code=404, detail="No users with open loans found")
    
    return users 