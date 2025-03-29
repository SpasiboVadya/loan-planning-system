"""Repository for plan operations."""

from datetime import date
from typing import List, Dict, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from components.plan.models import Plan
from components.credit.models import Credit
from components.payment.models import Payment
from components.dictionary.models import Dictionary
from components.plan import schemas


class PlanRepository:
    """Repository for plan operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_user_credits(self, user_id: int) -> List[schemas.UserCredit]:
        """Get all credits for a specific user with their payment history."""
        # Get user's credits
        result = await self.session.execute(
            select(Credit).where(Credit.user_id == user_id)
        )
        credits = result.scalars().all()
        
        if not credits:
            return []
        
        credits_data = []
        for credit in credits:
            # Get payments for this credit
            result = await self.session.execute(
                select(Payment)
                .where(Payment.credit_id == credit.id)
                .order_by(Payment.payment_date)
            )
            payments = result.scalars().all()
            
            # Get payment type names
            payment_types = {}
            for payment in payments:
                if payment.type_id not in payment_types:
                    result = await self.session.execute(
                        select(Dictionary.name).where(Dictionary.id == payment.type_id)
                    )
                    payment_types[payment.type_id] = result.scalar_one()
            
            credits_data.append(schemas.UserCredit(
                credit_id=credit.id,
                issuance_date=credit.issuance_date,
                return_date=credit.return_date,
                actual_return_date=credit.actual_return_date,
                body=float(credit.body),
                percent=float(credit.percent),
                payments=[
                    schemas.CreditPayment(
                        date=payment.payment_date,
                        sum=float(payment.sum),
                        type=payment_types[payment.type_id]
                    )
                    for payment in payments
                ]
            ))
        
        return credits_data

    async def insert_plans(self) -> bool:
        """Insert plans for the current month."""
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        
        # Get all categories from dictionary
        result = await self.session.execute(select(Dictionary))
        categories = result.scalars().all()
        
        # Create plans for each category
        for category in categories:
            # Check if plan already exists for this month and category
            existing_plan = await self.session.execute(
                select(Plan).where(
                    Plan.period == first_day_of_month,
                    Plan.category_id == category.id
                )
            )
            if existing_plan.scalar_one_or_none():
                continue
                
            # Calculate sum based on previous month's performance
            last_month = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
            
            # Get sum of payments for this category in the previous month
            result = await self.session.execute(
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
            self.session.add(new_plan)
        
        await self.session.commit()
        return True

    async def get_plans_performance(self, period: date) -> List[schemas.CategoryPerformance]:
        """Get performance of plans for a specific period."""
        # Get all plans for the period
        result = await self.session.execute(
            select(Plan).where(Plan.period == period)
        )
        plans = result.scalars().all()
        
        performance_data = []
        for plan in plans:
            # Get actual payments for this category in the period
            next_month = date(period.year, period.month + 1, 1) if period.month < 12 else date(period.year + 1, 1, 1)
            
            result = await self.session.execute(
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
            result = await self.session.execute(
                select(Dictionary.name).where(Dictionary.id == plan.category_id)
            )
            category_name = result.scalar_one()
            
            performance_data.append(schemas.CategoryPerformance(
                category=category_name,
                planned=float(plan.sum),
                actual=float(actual_sum),
                difference=float(actual_sum - plan.sum),
                performance_percentage=(actual_sum / plan.sum * 100) if plan.sum > 0 else 0
            ))
        
        return performance_data

    async def get_year_performance(self, year: int) -> schemas.YearPerformance:
        """Get yearly performance analysis with total sums per plan category."""
        year_data = {
            "year": year,
            "categories": {},
            "monthly_data": []
        }
        
        # Get all categories
        result = await self.session.execute(select(Dictionary))
        categories = result.scalars().all()
        
        # Initialize category data
        for category in categories:
            year_data["categories"][category.name] = {
                "total_planned": 0.0,
                "total_actual": 0.0,
                "monthly_data": [],
                "yearly_performance_percentage": 0.0
            }
        
        # Analyze each month
        for month in range(1, 13):
            period = date(year, month, 1)
            
            # Get plans for this month
            result = await self.session.execute(
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
                
                result = await self.session.execute(
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
                result = await self.session.execute(
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
            
            year_data["monthly_data"].append(month_data)
        
        # Calculate yearly performance percentages
        for category_name, category_data in year_data["categories"].items():
            if category_data["total_planned"] > 0:
                category_data["yearly_performance_percentage"] = (
                    category_data["total_actual"] / category_data["total_planned"] * 100
                )
            else:
                category_data["yearly_performance_percentage"] = 0
        
        return schemas.YearPerformance(**year_data)
