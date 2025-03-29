"""Payment model for the database."""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from components.core.database import Base


class Payment(Base):
    """Payment model for storing loan payments."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sum = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    credit_id = Column(Integer, ForeignKey("credits.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("dictionary.id"), nullable=False)

    # Relationships
    credit = relationship("Credit", back_populates="payments")
    payment_type = relationship("Dictionary", back_populates="payments") 