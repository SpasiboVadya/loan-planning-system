"""Repository for plan operations."""

from datetime import date, datetime
from typing import List, Dict, Tuple, BinaryIO
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import csv

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
        """
        Get all credits for a specific user with their payment history.
        
        Returns a list of user credits with the following information:
        - Date the loan was issued
        - Boolean value whether the loan is closed
        - For closed loans:
            - Date of loan repayment
            - Loan amount disbursed
            - Accrued interest
            - Amount of payments on the loan
        - For open loans:
            - Loan repayment deadline
            - Number of days the loan is overdue
            - The amount of the loan
            - Accrued interest
            - The amount of payments on the body
            - Amount of interest payments
        """
        # Get user's credits
        result = await self.session.execute(
            select(Credit).where(Credit.user_id == user_id)
        )
        credits = result.scalars().all()
        
        if not credits:
            return []
        
        credits_data = []
        
        # Get dictionary categories to identify payment types
        result = await self.session.execute(select(Dictionary))
        categories = {category.id: category.name for category in result.scalars().all()}
        
        # Find category IDs for body and interest payments
        # Assuming тіло (body) is for credit body payments, відсотки (interest) is for interest payments
        body_category_id = next((k for k, v in categories.items() if v == "тіло"), None)
        interest_category_id = next((k for k, v in categories.items() if v == "відсотки"), None)
        
        for credit in credits:
            # Get payments for this credit
            result = await self.session.execute(
                select(Payment)
                .where(Payment.credit_id == credit.id)
                .order_by(Payment.payment_date)
            )
            payments = result.scalars().all()
            
            # Calculate payment amounts by type
            total_payment_amount = sum(float(payment.sum) for payment in payments)
            body_payments = sum(
                float(payment.sum) 
                for payment in payments 
                if payment.type_id == body_category_id
            )
            interest_payments = sum(
                float(payment.sum) 
                for payment in payments 
                if payment.type_id == interest_category_id
            )
            
            # Check if loan is closed (has actual return date)
            is_closed = credit.actual_return_date is not None
            
            # Create the UserCredit object
            user_credit = schemas.UserCredit(
                credit_id=credit.id,
                issuance_date=credit.issuance_date,
                is_closed=is_closed
            )
            
            if is_closed:
                # For closed loans
                # Convert actual_return_date to date if it's a datetime
                repayment_date = credit.actual_return_date.date() if isinstance(credit.actual_return_date, datetime) else credit.actual_return_date
                
                user_credit.closed_loan_data = schemas.ClosedLoanData(
                    repayment_date=repayment_date,
                    loan_amount=float(credit.body),
                    accrued_interest=float(credit.percent),
                    payment_amount=total_payment_amount
                )
            else:
                # For open loans
                # Calculate overdue days
                today = date.today()
                
                # Convert return_date to date if it's a datetime
                return_date = credit.return_date.date() if isinstance(credit.return_date, datetime) else credit.return_date
                
                overdue_days = max(0, (today - return_date).days) if today > return_date else 0
                
                user_credit.open_loan_data = schemas.OpenLoanData(
                    repayment_deadline=return_date,
                    overdue_days=overdue_days,
                    loan_amount=float(credit.body),
                    accrued_interest=float(credit.percent),
                    body_payments=body_payments,
                    interest_payments=interest_payments
                )
            
            credits_data.append(user_credit)
        
        return credits_data


    async def get_plans_performance(self, as_of_date: date) -> List[schemas.CategoryPerformance]:
        """
        Get performance of plans as of a specific date.
        
        Args:
            as_of_date: The date as of which to check plan execution
            
        Returns:
            List of category performances with:
            - Month of the plan
            - Plan category
            - Amount from the plan
            - Amount of credits issued or payments collected
            - % of plan fulfillment
        """
        # Determine the month of the given date
        plan_month = date(as_of_date.year, as_of_date.month, 1)
        
        # Get all plans for the month
        result = await self.session.execute(
            select(Plan).where(Plan.period == plan_month)
        )
        plans = result.scalars().all()
        
        if not plans:
            return []
        
        # Get dictionary categories to identify issue and collection categories
        result = await self.session.execute(select(Dictionary))
        categories = {category.id: category.name for category in result.scalars().all()}
        
        # Find category IDs for issue and collection
        # Using the actual names from the output: "видача" (issue) and "збір" (collection)
        issue_category_id = next((k for k, v in categories.items() if v == "видача"), None)
        collection_category_id = next((k for k, v in categories.items() if v == "збір"), None)
        

        performance_data = []
        
        for plan in plans:
            category_id = plan.category_id
            category_name = categories.get(category_id, f"Category {category_id}")
            
            # Calculate actual amounts depending on category
            if category_id == issue_category_id:
                # For "Issue" category - sum of credit.body for credits issued in this period
                query = select(func.sum(Credit.body)).where(
                    Credit.issuance_date >= plan_month,
                    Credit.issuance_date <= as_of_date
                )
                result = await self.session.execute(query)
                actual_amount = result.scalar() or 0
            elif category_id == collection_category_id:
                # For "Collection" category - sum of payments in this period
                query = select(func.sum(Payment.sum)).join(Credit, Payment.credit_id == Credit.id).where(
                    Payment.payment_date >= plan_month,
                    Payment.payment_date <= as_of_date,
                    Payment.type_id == category_id
                )
                result = await self.session.execute(query)
                actual_amount = result.scalar() or 0
            else:
                # For other categories - sum of payments of that type
                query = select(func.sum(Payment.sum)).join(Credit, Payment.credit_id == Credit.id).where(
                    Payment.payment_date >= plan_month,
                    Payment.payment_date <= as_of_date,
                    Payment.type_id == category_id
                )
                result = await self.session.execute(query)
                actual_amount = result.scalar() or 0

            # Calculate fulfillment percentage
            plan_amount = float(plan.sum)
            actual_amount = float(actual_amount)
            fulfillment_percentage = (actual_amount / plan_amount * 100) if plan_amount > 0 else 0
            

            # Add to result
            performance_data.append(schemas.CategoryPerformance(
                plan_month=plan_month,
                category=category_name,
                amount_from_the_plan=plan_amount,
                issued_credits_or_payments=actual_amount,
                performance_percentage=fulfillment_percentage
            ))
        
        return performance_data

    async def get_year_performance(self, year: int) -> schemas.YearSummary:
        """
        Get summarized information for a given year, grouped by month.
        
        Returns monthly summaries with:
        - Month and year
        - Number of credits issued for the month (num_credits_issued)
        - Amount from the issue plan for the month (issue_plan_amount)
        - Amount of issued credits for the month (issued_credits_amount)
        - % fulfillment of the issue plan (issue_plan_fulfillment_percentage)
        - Number of payments per month (num_payments)
        - Amount from the collection plan for the month (collection_plan_amount)
        - Amount of collected payments for the month (collected_payments_amount)
        - % fulfillment of the collection plan (collection_plan_fulfillment_percentage)
        - % of the amount of issues for the month from the amount of issues for the year (issues_percentage_of_year)
        - % of the amount of payments for the month from the amount of payments for the year (payments_percentage_of_year)
        """
        # Initialize the yearly totals
        total_credits_issued = 0
        total_num_payments = 0
        total_issued_credits_amount = 0
        total_issued_credits_plan_amount = 0
        total_collection_plan_amount = 0
        total_collected_payments_amount = 0
        
        # Get dictionary categories to identify payment types
        result = await self.session.execute(select(Dictionary))
        categories = {category.id: category.name for category in result.scalars().all()}
        
        # Find category IDs for issue and collection
        # Using the actual names from the output: "видача" (issue) and "збір" (collection)
        issue_category_id = next((k for k, v in categories.items() if v == "видача"), None)
        collection_category_id = next((k for k, v in categories.items() if v == "збір"), None)
        
        # Get yearly data for credits issued
        result = await self.session.execute(
            select(Credit)
            .where(
                Credit.issuance_date >= date(year, 1, 1),
                Credit.issuance_date < date(year + 1, 1, 1)
            )
        )
        yearly_credits = list(result.scalars().all())
        total_credits_issued = len(yearly_credits)
        yearly_credit_amount = sum(float(credit.body) for credit in yearly_credits)
        total_issued_credits_amount = yearly_credit_amount
        
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
        total_num_payments = len(yearly_payments)
        yearly_payment_amount = sum(float(payment.sum) for payment in yearly_payments)
        
        # Split payments by category
        collection_payments = [p for p in yearly_payments if p.type_id == collection_category_id]
        total_collected_payments_amount = sum(float(payment.sum) for payment in collection_payments)
        
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
            if plan.category_id == issue_category_id:
                total_issued_credits_plan_amount += float(plan.sum)
            elif plan.category_id == collection_category_id:
                total_collection_plan_amount += float(plan.sum)
        
        # Calculate overall percentages
        overall_issue_plan_fulfillment_percentage = (
            (total_issued_credits_amount / total_issued_credits_plan_amount * 100) 
            if total_issued_credits_plan_amount > 0 else 0
        )
        overall_collection_plan_fulfillment_percentage = (
            (total_collected_payments_amount / total_collection_plan_amount * 100) 
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
            month_num_credits_issued = len(month_credits)
            month_issued_credits_amount = sum(float(credit.body) for credit in month_credits)
            
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
            
            # Split payments by category
            month_collected_payments = [p for p in month_payments if p.type_id == collection_category_id]
            month_collected_payments_amount = sum(float(payment.sum) for payment in month_collected_payments)
            
            # Get plan amounts for this month
            result = await self.session.execute(
                select(Plan)
                .where(
                    Plan.period == month_start
                )
            )
            month_plans = list(result.scalars().all())
            
            # Get plan amounts by category for this month
            month_issue_plan_amount = sum(
                float(plan.sum) 
                for plan in month_plans 
                if plan.category_id == issue_category_id
            )
            month_collection_plan_amount = sum(
                float(plan.sum) 
                for plan in month_plans 
                if plan.category_id == collection_category_id
            )
            
            # Calculate percentages
            month_issue_plan_fulfillment_percentage = (
                (month_issued_credits_amount / month_issue_plan_amount * 100) 
                if month_issue_plan_amount > 0 else 0
            )
            month_collection_plan_fulfillment_percentage = (
                (month_collected_payments_amount / month_collection_plan_amount * 100) 
                if month_collection_plan_amount > 0 else 0
            )
            month_issues_percentage_of_year = (
                (month_issued_credits_amount / yearly_credit_amount * 100) 
                if yearly_credit_amount > 0 else 0
            )
            month_payments_percentage_of_year = (
                (month_payment_amount / yearly_payment_amount * 100) 
                if yearly_payment_amount > 0 else 0
            )
            
            # Add the monthly summary
            monthly_summaries.append(schemas.MonthSummary(
                month=month,
                year=year,
                num_credits_issued=month_num_credits_issued,
                issue_plan_amount=month_issue_plan_amount,
                issued_credits_amount=month_issued_credits_amount,
                issue_plan_fulfillment_percentage=month_issue_plan_fulfillment_percentage,
                num_payments=month_num_payments,
                collection_plan_amount=month_collection_plan_amount,
                collected_payments_amount=month_collected_payments_amount,
                collection_plan_fulfillment_percentage=month_collection_plan_fulfillment_percentage,
                issues_percentage_of_year=month_issues_percentage_of_year,
                payments_percentage_of_year=month_payments_percentage_of_year
            ))
        
        # Create and return the year summary
        return schemas.YearSummary(
            year=year,
            total_credits_issued=total_credits_issued,
            total_issue_plan_amount=total_issued_credits_plan_amount,
            total_issued_credits_amount=total_issued_credits_amount,
            overall_issue_plan_fulfillment_percentage=overall_issue_plan_fulfillment_percentage,
            total_num_payments=total_num_payments,
            total_collection_plan_amount=total_collection_plan_amount,
            total_collected_payments_amount=total_collected_payments_amount,
            overall_collection_plan_fulfillment_percentage=overall_collection_plan_fulfillment_percentage,
            monthly_summaries=monthly_summaries
        )


    async def upload_plans_from_csv(self, file_content: BinaryIO) -> Tuple[bool, str, List[Dict]]:
        """
        Upload plans from a CSV file.
        
        Args:
            file_content: The CSV file content
            
        Returns:
            Tuple containing:
            - Success status (bool)
            - Message (str)
            - List of errors if any (List[Dict])
        """
        errors = []
        
        try:
            # Read CSV file
            content_str = file_content.read().decode('utf-8')
            csv_reader = csv.DictReader(content_str.splitlines(), delimiter='\t')
            
            # Store rows for later processing
            csv_rows = list(csv_reader)
            
            # Validate all rows first
            for row_num, row in enumerate(csv_rows, start=2):  # Start at 2 to account for header row
                # Validate required fields
                if not all(field in row for field in ['period', 'sum', 'category_id']):
                    return False, "CSV file must contain 'period', 'sum', and 'category_id' columns", []
                
                # Validate period format and first day of month
                try:
                    # Parse date in format DD.MM.YYYY
                    day, month, year = map(int, row['period'].split('.'))
                    plan_month = date(year, month, day)
                    
                    # Check if it's the first day of the month
                    if plan_month.day != 1:
                        errors.append({
                            "row": row_num,
                            "message": f"Period must be the first day of the month (got {plan_month})"
                        })
                        continue
                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "message": f"Invalid date format for period: {row['period']}. Expected DD.MM.YYYY"
                    })
                    continue
                
                # Validate sum
                try:
                    amount = float(row['sum'])
                    if pd.isna(amount):
                        errors.append({
                            "row": row_num,
                            "message": "Sum cannot be empty"
                        })
                        continue
                except Exception:
                    errors.append({
                        "row": row_num,
                        "message": f"Invalid sum value: {row['sum']}"
                    })
                    continue
                
                # Validate category_id
                try:
                    category_id = int(row['category_id'])
                    
                    # Check if category exists
                    result = await self.session.execute(
                        select(Dictionary).where(Dictionary.id == category_id)
                    )
                    if not result.scalar_one_or_none():
                        errors.append({
                            "row": row_num,
                            "message": f"Category ID {category_id} does not exist"
                        })
                        continue
                except Exception:
                    errors.append({
                        "row": row_num,
                        "message": f"Invalid category_id: {row['category_id']}"
                    })
                    continue
                
                # Check if plan already exists
                existing_plan = await self.session.execute(
                    select(Plan).where(
                        Plan.period == plan_month,
                        Plan.category_id == category_id
                    )
                )
                if existing_plan.scalar_one_or_none():
                    errors.append({
                        "row": row_num,
                        "message": f"Plan already exists for {plan_month} with category_id {category_id}"
                    })
                    continue
            
            # If we have any errors, return them without committing
            if errors:
                return False, "Validation errors occurred", errors
            
            # If no errors, process all rows and insert the plans
            for row in csv_rows:
                day, month, year = map(int, row['period'].split('.'))
                plan_month = date(year, month, day)
                category_id = int(row['category_id'])
                amount = float(row['sum'])
                
                # Create and add plan
                new_plan = Plan(
                    period=plan_month,
                    sum=amount,
                    category_id=category_id
                )
                self.session.add(new_plan)
            
            # Commit all changes
            await self.session.commit()
            return True, "Plans uploaded successfully", []
            
        except Exception as e:
            # Handle any unexpected errors
            return False, f"Error processing file: {str(e)}", []
