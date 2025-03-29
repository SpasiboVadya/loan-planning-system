"""Credit model for the database."""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from components.core.database import Base


class Credit(Base):
    """Credit model representing a loan in the system."""
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    issuance_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=False)
    actual_return_date = Column(DateTime, nullable=True)
    body = Column(Numeric(10, 2), nullable=False)
    percent = Column(Numeric(10, 2), nullable=False)

    # Relationships
    user = relationship("User", back_populates="credits")
    payments = relationship("Payment", back_populates="credit") 