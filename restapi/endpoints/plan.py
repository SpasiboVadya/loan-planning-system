"""Plan endpoints for the API."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.init_db import get_db
from components.plan.models import Plan
from components.credit.models import Credit
from components.payment.models import Payment
from components.dictionary.models import Dictionary
from restapi.endpoints.auth import get_current_user
from components.user.models import User

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    responses={404: {"description": "Not found"}},
)

@router.get("/user_credits/{user_id}")
async def get_user_credits(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all credits for a specific user with their payment history."""
    # Get user's credits
    result = await db.execute(
        select(Credit).where(Credit.user_id == user_id)
    )
    credits = result.scalars().all()
    
    if not credits:
        raise HTTPException(status_code=404, detail="No credits found for this user")
    
    credits_data = []
    for credit in credits:
        # Get payments for this credit
        result = await db.execute(
            select(Payment)
            .where(Payment.credit_id == credit.id)
            .order_by(Payment.payment_date)
        )
        payments = result.scalars().all()
        
        # Get payment type names
        payment_types = {}
        for payment in payments:
            if payment.type_id not in payment_types:
                result = await db.execute(
                    select(Dictionary.name).where(Dictionary.id == payment.type_id)
                )
                payment_types[payment.type_id] = result.scalar_one()
        
        credits_data.append({
            "credit_id": credit.id,
            "issuance_date": credit.issuance_date,
            "return_date": credit.return_date,
            "actual_return_date": credit.actual_return_date,
            "body": float(credit.body),
            "percent": float(credit.percent),
            "payments": [
                {
                    "date": payment.payment_date,
                    "sum": float(payment.sum),
                    "type": payment_types[payment.type_id]
                }
                for payment in payments
            ]
        })
    
    return credits_data

@router.post("/insert")
async def insert_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Insert plans for the current month."""
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    
    # Get all categories from dictionary
    result = await db.execute(select(Dictionary))
    categories = result.scalars().all()
    
    # Create plans for each category
    for category in categories:
        # Check if plan already exists for this month and category
        existing_plan = await db.execute(
            select(Plan).where(
                Plan.period == first_day_of_month,
                Plan.category_id == category.id
            )
        )
        if existing_plan.scalar_one_or_none():
            continue
            
        # Calculate sum based on previous month's performance
        # This is a simplified example - you might want to adjust the calculation
        last_month = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
        
        # Get sum of payments for this category in the previous month
        result = await db.execute(
            select(func.sum(Payment.sum))
            .join(Credit, Payment.credit_id == Credit.id)
            .where(
                Payment.payment_date >= last_month,
                Payment.payment_date < first_day_of_month,
                Payment.type_id == category.id
            )
        )
        previous_sum = result.scalar() or 0
        
        # Create new plan
        new_plan = Plan(
            period=first_day_of_month,
            sum=previous_sum * 1.1,  # 10% increase from previous month
            category_id=category.id
        )
        db.add(new_plan)
    
    await db.commit()
    return {"message": "Plans inserted successfully"}

@router.get("/performance")
async def get_plans_performance(
    period: date = Query(..., description="Period to check (first day of the month)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance of plans for a specific period."""
    # Get all plans for the period
    result = await db.execute(
        select(Plan).where(Plan.period == period)
    )
    plans = result.scalars().all()
    
    performance_data = []
    for plan in plans:
        # Get actual payments for this category in the period
        next_month = date(period.year, period.month + 1, 1) if period.month < 12 else date(period.year + 1, 1, 1)
        
        result = await db.execute(
            select(func.sum(Payment.sum))
            .join(Credit, Payment.credit_id == Credit.id)
            .where(
                Payment.payment_date >= period,
                Payment.payment_date < next_month,
                Payment.type_id == plan.category_id
            )
        )
        actual_sum = result.scalar() or 0
        
        # Get category name
        result = await db.execute(
            select(Dictionary.name).where(Dictionary.id == plan.category_id)
        )
        category_name = result.scalar_one()
        
        performance_data.append({
            "category": category_name,
            "planned": float(plan.sum),
            "actual": float(actual_sum),
            "difference": float(actual_sum - plan.sum),
            "performance_percentage": (actual_sum / plan.sum * 100) if plan.sum > 0 else 0
        })
    
    return performance_data

@router.get("/year-performance")
async def get_year_performance(
    year: int = Query(..., description="Year to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get yearly performance analysis with total sums per plan category."""
    year_data = {
        "year": year,
        "categories": {}
    }
    
    # Get all categories
    result = await db.execute(select(Dictionary))
    categories = result.scalars().all()
    
    # Initialize category data
    for category in categories:
        year_data["categories"][category.name] = {
            "total_planned": 0.0,
            "total_actual": 0.0,
            "monthly_data": []
        }
    
    # Analyze each month
    for month in range(1, 13):
        period = date(year, month, 1)
        
        # Get plans for this month
        result = await db.execute(
            select(Plan).where(Plan.period == period)
        )
        plans = result.scalars().all()
        
        month_data = {
            "month": month,
            "categories": {}
        }
        
        for plan in plans:
            # Get actual payments for this category in the period
            next_month = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
            
            result = await db.execute(
                select(func.sum(Payment.sum))
                .join(Credit, Payment.credit_id == Credit.id)
                .where(
                    Payment.payment_date >= period,
                    Payment.payment_date < next_month,
                    Payment.type_id == plan.category_id
                )
            )
            actual_sum = result.scalar() or 0
            
            # Get category name
            result = await db.execute(
                select(Dictionary.name).where(Dictionary.id == plan.category_id)
            )
            category_name = result.scalar_one()
            
            # Update monthly data
            month_data["categories"][category_name] = {
                "planned": float(plan.sum),
                "actual": float(actual_sum),
                "difference": float(actual_sum - plan.sum),
                "performance_percentage": (actual_sum / plan.sum * 100) if plan.sum > 0 else 0
            }
            
            # Update yearly totals
            year_data["categories"][category_name]["total_planned"] += float(plan.sum)
            year_data["categories"][category_name]["total_actual"] += float(actual_sum)
            year_data["categories"][category_name]["monthly_data"].append(month_data["categories"][category_name])
        
        year_data["monthly_data"] = year_data.get("monthly_data", []) + [month_data]
    
    # Calculate yearly performance percentages
    for category_data in year_data["categories"].values():
        if category_data["total_planned"] > 0:
            category_data["yearly_performance_percentage"] = (
                category_data["total_actual"] / category_data["total_planned"] * 100
            )
        else:
            category_data["yearly_performance_percentage"] = 0
    
    return year_data 