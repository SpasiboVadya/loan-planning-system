"""User model for the database."""

from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from components.core.database import Base


class User(Base):
    """User model representing a client in the system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    registration_date = Column(Date, nullable=False)

    # Relationship with Credits
    credits = relationship("Credit", back_populates="user", foreign_keys="Credit.user_id")
