"""Dictionary model for the database."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from components.core.database import Base


class Dictionary(Base):
    """Dictionary model for storing reference data."""
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Relationships
    plans = relationship("Plan", back_populates="category")
    payments = relationship("Payment", back_populates="payment_type")
