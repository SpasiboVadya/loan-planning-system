"""Repository for user operations."""

from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from components.user.models import User
from components.user.schemas import UserCreate, User as UserSchema, UserUpdate
from components.core.security import get_password_hash
from components.credit.models import Credit
from components.plan import schemas as plan_schemas


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

    async def update(self, user_id: int, user: UserUpdate) -> Optional[UserSchema]:
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

    async def get_users_with_open_loans(self) -> List[Dict]:
        """
        Get all users who have open loans.
        
        Returns a list of users with open loan information.
        """
        # Find users with credits where actual_return_date is NULL (open loans)
        result = await self.session.execute(
            select(Credit.user_id)
            .where(Credit.actual_return_date == None)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]
        
        if not user_ids:
            return []
        
        # Get user information for these IDs
        users_with_loans = []
        
        for user_id in user_ids:
            # Get user info
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Get open loans for this user
                # We need to use the PlanRepository for this
                from components.plan.repository import PlanRepository
                plan_repo = PlanRepository(self.session)
                credits = await plan_repo.get_user_credits(user_id)
                
                # Filter only open loans
                open_loans = [credit for credit in credits if not credit.is_closed]
                
                if open_loans:
                    users_with_loans.append({
                        "user_id": user.id,
                        "login": user.login,
                        "registration_date": user.registration_date,
                        "open_loans": open_loans
                    })
        
        return users_with_loans
