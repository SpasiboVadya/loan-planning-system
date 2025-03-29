"""Plan model for the database."""

from sqlalchemy import Column, Integer, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from components.core.database import Base


class Plan(Base):
    """Plan model for storing planned loan amounts."""
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(Date, nullable=False)  # First day of the month
    sum = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("dictionary.id"), nullable=False)

    # Relationship with Dictionary
    category = relationship("Dictionary", back_populates="plans") 