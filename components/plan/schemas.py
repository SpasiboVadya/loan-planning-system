"""Pydantic schemas for plan data validation."""

from datetime import date
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
    category: str
    planned: float
    actual: float
    difference: float
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


class CreditPayment(BaseModel):
    """Schema for credit payment."""
    date: date
    sum: float
    type: str


class UserCredit(BaseModel):
    """Schema for user credit."""
    credit_id: int
    issuance_date: date
    return_date: date
    actual_return_date: Optional[date] = None
    body: float
    percent: float
    payments: List[CreditPayment]
