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

    async def get_year_summary(self, year: int) -> schemas.YearSummary:
        """
        Get summarized information for a given year, grouped by month.
        
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
        # Initialize the yearly totals
        total_issues = 0
        total_payments = 0
        total_payment_amount = 0
        total_plan_amount = 0
        total_collection_plan_amount = 0
        total_collection_payments = 0
        
        # Get dictionary categories to identify payment types
        result = await self.session.execute(select(Dictionary))
        categories = {category.id: category.name for category in result.scalars().all()}
        
        # Find category IDs for body and interest payments
        # Assuming тіло (body) is for credit issue, відсотки (interest) is for collection
        body_category_id = next((k for k, v in categories.items() if v == "тіло"), None)
        interest_category_id = next((k for k, v in categories.items() if v == "відсотки"), None)
        
        # Get yearly data for credits issued
        result = await self.session.execute(
            select(Credit)
            .where(
                Credit.issuance_date >= date(year, 1, 1),
                Credit.issuance_date < date(year + 1, 1, 1)
            )
        )
        yearly_credits = list(result.scalars().all())
        total_issues = len(yearly_credits)
        yearly_credit_amount = sum(float(credit.body) for credit in yearly_credits)
        
        # Get yearly data for payments
        result = await self.session.execute(
            select(Payment)
            .join(Credit, Payment.credit_id == Credit.id)
            .where(
                Payment.payment_date >= date(year, 1, 1),
                Payment.payment_date < date(year + 1, 1, 1)
            )
        )
        yearly_payments = list(result.scalars().all())
        total_payments = len(yearly_payments)
        yearly_payment_amount = sum(float(payment.sum) for payment in yearly_payments)
        
        # Get yearly plan amounts
        result = await self.session.execute(
            select(Plan)
            .where(
                Plan.period >= date(year, 1, 1),
                Plan.period < date(year + 1, 1, 1)
            )
        )
        yearly_plans = list(result.scalars().all())
        
        # Get plan amounts by category
        for plan in yearly_plans:
            if plan.category_id == body_category_id:
                total_plan_amount += float(plan.sum)
            elif plan.category_id == interest_category_id:
                total_collection_plan_amount += float(plan.sum)
        
        # Calculate overall percentages
        overall_plan_fulfillment = (
            (total_payment_amount / total_plan_amount * 100) if total_plan_amount > 0 else 0
        )
        overall_collection_plan_fulfillment = (
            (total_collection_payments / total_collection_plan_amount * 100) 
            if total_collection_plan_amount > 0 else 0
        )
        
        # Initialize monthly summaries
        monthly_summaries = []
        
        # Process each month
        for month in range(1, 13):
            month_start = date(year, month, 1)
            month_end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
            
            # Get credits issued in this month
            result = await self.session.execute(
                select(Credit)
                .where(
                    Credit.issuance_date >= month_start,
                    Credit.issuance_date < month_end
                )
            )
            month_credits = list(result.scalars().all())
            month_num_issues = len(month_credits)
            month_issues_amount = sum(float(credit.body) for credit in month_credits)
            
            # Get payments made in this month
            result = await self.session.execute(
                select(Payment)
                .join(Credit, Payment.credit_id == Credit.id)
                .where(
                    Payment.payment_date >= month_start,
                    Payment.payment_date < month_end
                )
            )
            month_payments = list(result.scalars().all())
            month_num_payments = len(month_payments)
            month_payment_amount = sum(float(payment.sum) for payment in month_payments)
            
            # Split payments by type
            month_body_payments = sum(
                float(payment.sum) 
                for payment in month_payments 
                if payment.type_id == body_category_id
            )
            month_interest_payments = sum(
                float(payment.sum) 
                for payment in month_payments 
                if payment.type_id == interest_category_id
            )
            
            # Get plan amounts for this month
            result = await self.session.execute(
                select(Plan)
                .where(
                    Plan.period == month_start
                )
            )
            month_plans = list(result.scalars().all())
            
            # Get plan amounts by category for this month
            month_plan_amount = sum(
                float(plan.sum) 
                for plan in month_plans 
                if plan.category_id == body_category_id
            )
            month_collection_plan_amount = sum(
                float(plan.sum) 
                for plan in month_plans 
                if plan.category_id == interest_category_id
            )
            
            # Calculate percentages
            month_plan_fulfillment = (
                (month_body_payments / month_plan_amount * 100) 
                if month_plan_amount > 0 else 0
            )
            month_collection_plan_fulfillment = (
                (month_interest_payments / month_collection_plan_amount * 100) 
                if month_collection_plan_amount > 0 else 0
            )
            month_issues_percentage = (
                (month_issues_amount / yearly_credit_amount * 100) 
                if yearly_credit_amount > 0 else 0
            )
            month_payments_percentage = (
                (month_payment_amount / yearly_payment_amount * 100) 
                if yearly_payment_amount > 0 else 0
            )
            
            # Add the monthly summary
            monthly_summaries.append(schemas.MonthSummary(
                month=month,
                year=year,
                num_issues=month_num_issues,
                plan_amount=month_plan_amount,
                total_payments=month_body_payments,
                plan_fulfillment_percentage=month_plan_fulfillment,
                num_payments=month_num_payments,
                collection_plan_amount=month_collection_plan_amount,
                collection_payments=month_interest_payments,
                collection_plan_fulfillment_percentage=month_collection_plan_fulfillment,
                issues_percentage_of_year=month_issues_percentage,
                payments_percentage_of_year=month_payments_percentage
            ))
            
            # Update yearly totals
            total_payment_amount += month_body_payments
            total_collection_payments += month_interest_payments
        
        # Create and return the year summary
        return schemas.YearSummary(
            year=year,
            total_issues=total_issues,
            total_plan_amount=total_plan_amount,
            total_payments=total_payment_amount,
            overall_plan_fulfillment_percentage=overall_plan_fulfillment,
            total_num_payments=total_payments,
            total_collection_plan_amount=total_collection_plan_amount,
            total_collection_payments=total_collection_payments,
            overall_collection_plan_fulfillment_percentage=overall_collection_plan_fulfillment,
            monthly_summaries=monthly_summaries
        )
