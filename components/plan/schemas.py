"""Pydantic schemas for plan data validation."""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PlanBase(BaseModel):
    """Base plan schema."""
    period: date
    sum: float
    category_id: int


class PlanCreate(PlanBase):
    """Schema for plan creation."""
    pass


class PlanInDB(PlanBase):
    """Schema for plan in database."""
    id: int

    class Config:
        from_attributes = True


class Plan(PlanInDB):
    """Schema for plan response."""
    pass


class CategoryPerformance(BaseModel):
    """Schema for category performance."""
    plan_month: date
    category: str
    amount_from_the_plan: float
    issued_credits_or_payments: float
    performance_percentage: float


class MonthlyPerformance(BaseModel):
    """Schema for monthly performance."""
    month: int
    categories: Dict[str, Any]


class CategoryYearlyData(BaseModel):
    """Schema for category yearly data."""
    total_planned: float
    total_actual: float
    monthly_data: List[Any]
    yearly_performance_percentage: float = 0


class YearPerformance(BaseModel):
    """Schema for yearly performance."""
    year: int
    categories: Dict[str, CategoryYearlyData]
    monthly_data: Optional[List[MonthlyPerformance]] = None


class MonthSummary(BaseModel):
    """Schema for monthly summary performance."""
    month: int
    year: int
    num_credits_issued: int
    issue_plan_amount: float
    issued_credits_amount: float
    issue_plan_fulfillment_percentage: float
    num_payments: int
    collection_plan_amount: float
    collected_payments_amount: float
    collection_plan_fulfillment_percentage: float
    issues_percentage_of_year: float
    payments_percentage_of_year: float


class YearSummary(BaseModel):
    """Schema for yearly summary performance."""
    year: int
    total_credits_issued: int
    total_issue_plan_amount: float
    total_issued_credits_amount: float
    overall_issue_plan_fulfillment_percentage: float
    total_num_payments: int
    total_collection_plan_amount: float
    total_collected_payments_amount: float
    overall_collection_plan_fulfillment_percentage: float
    monthly_summaries: List[MonthSummary]


class CreditPayment(BaseModel):
    """Schema for credit payment."""
    date: date
    sum: float
    type: str


class ClosedLoanData(BaseModel):
    """Schema for closed loan data."""
    repayment_date: date
    loan_amount: float
    accrued_interest: float
    payment_amount: float


class OpenLoanData(BaseModel):
    """Schema for open loan data."""
    repayment_deadline: date
    overdue_days: int
    loan_amount: float
    accrued_interest: float
    body_payments: float
    interest_payments: float


class UserCredit(BaseModel):
    """Schema for user credit."""
    credit_id: int
    issuance_date: date
    is_closed: bool
    closed_loan_data: Optional[ClosedLoanData] = None
    open_loan_data: Optional[OpenLoanData] = None


class UserWithOpenLoans(BaseModel):
    """Schema for user with open loans."""
    user_id: int
    login: str
    registration_date: date
    open_loans: List[UserCredit]


class PlanUploadError(BaseModel):
    """Schema for plan upload error."""
    row: int
    message: str


class PlanUploadResponse(BaseModel):
    """Schema for plan upload response."""
    success: bool
    message: str
    errors: Optional[List[PlanUploadError]] = None
