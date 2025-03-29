"""Script to seed test data into the database."""

from datetime import date, datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from components.core.init_db import get_db
from components.user.models import User
from components.credit.models import Credit
from components.payment.models import Payment
from components.plan.models import Plan
from components.dictionary.models import Dictionary
from components.core.security import get_password_hash

async def seed_data():
    """Seed test data into the database."""
    async for db in get_db():
        # Clear existing data
        await db.execute("DELETE FROM payments")
        await db.execute("DELETE FROM credits")
        await db.execute("DELETE FROM plans")
        await db.execute("DELETE FROM dictionary")
        await db.execute("DELETE FROM users")
        
        # Create dictionary entries
        categories = [
            Dictionary(name="Principal"),
            Dictionary(name="Interest"),
            Dictionary(name="Late Fee"),
            Dictionary(name="Processing Fee")
        ]
        for category in categories:
            db.add(category)
        await db.commit()
        
        # Create users
        users = [
            User(
                login="john_doe",
                password=get_password_hash("password123"),
                registration_date=date(2024, 1, 1)
            ),
            User(
                login="jane_smith",
                password=get_password_hash("password123"),
                registration_date=date(2024, 1, 15)
            ),
            User(
                login="bob_wilson",
                password=get_password_hash("password123"),
                registration_date=date(2024, 2, 1)
            )
        ]
        for user in users:
            db.add(user)
        await db.commit()
        
        # Create credits
        credits = []
        for user in users:
            for i in range(2):  # 2 credits per user
                credit = Credit(
                    user_id=user.id,
                    issuance_date=datetime(2024, 1, 1) + timedelta(days=i*30),
                    return_date=datetime(2024, 12, 31),
                    body=10000.00,
                    percent=12.5
                )
                credits.append(credit)
                db.add(credit)
        await db.commit()
        
        # Create payments
        payment_types = await db.execute("SELECT id FROM dictionary")
        payment_type_ids = [row[0] for row in payment_types]
        
        for credit in credits:
            # Create multiple payments for each credit
            for i in range(3):
                payment = Payment(
                    sum=1000.00 + i * 100,
                    payment_date=datetime(2024, 1, 1) + timedelta(days=i*30),
                    credit_id=credit.id,
                    type_id=payment_type_ids[i % len(payment_type_ids)]
                )
                db.add(payment)
        await db.commit()
        
        # Create plans
        for month in range(1, 4):  # Plans for first 3 months
            for category in categories:
                plan = Plan(
                    period=date(2024, month, 1),
                    sum=50000.00 + month * 10000,
                    category_id=category.id
                )
                db.add(plan)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_data()) 