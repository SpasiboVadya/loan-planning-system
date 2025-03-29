"""Repository for user operations."""

from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from components.user.models import User
from components.user.schemas import UserCreate, User as UserSchema
from components.core.security import get_password_hash


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, user: UserCreate) -> UserSchema:
        """Create a new user."""
        db_user = User(
            login=user.login,
            password=get_password_hash(user.password),
            registration_date=date.today()
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_by_id(self, user_id: int) -> Optional[UserSchema]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> Optional[UserSchema]:
        """Get user by login."""
        result = await self.session.execute(
            select(User).where(User.login == login)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        registration_date_from: Optional[date] = None,
        registration_date_to: Optional[date] = None
    ) -> List[UserSchema]:
        """Get all users with optional filtering."""
        query = select(User)
        
        if registration_date_from:
            query = query.where(User.registration_date >= registration_date_from)
        if registration_date_to:
            query = query.where(User.registration_date <= registration_date_to)
            
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, user_id: int, user: UserCreate) -> Optional[UserSchema]:
        """Update user by ID."""
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None

        db_user.login = user.login
        if user.password:
            db_user.password = get_password_hash(user.password)

        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return False

        await self.session.delete(db_user)
        await self.session.commit()
        return True

    async def exists(self, login: str) -> bool:
        """Check if user with given login exists."""
        result = await self.session.execute(
            select(User.id).where(User.login == login)
        )
        return result.scalar_one_or_none() is not None

    async def get_users_with_credits(self) -> List[UserSchema]:
        """Get all users who have credits."""
        result = await self.session.execute(
            select(User).join(User.credits).distinct()
        )
        return list(result.scalars().all())
