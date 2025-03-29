"""Script to import test data from CSV files into the database."""

import asyncio
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from components.core.init_db import get_db
from components.user.models import User
from components.credit.models import Credit
from components.payment.models import Payment
from components.plan.models import Plan
from components.dictionary.models import Dictionary
from components.core.security import get_password_hash

# Format date strings to Python datetime objects
def parse_date(date_str):
    """Parse date string in DD.MM.YYYY format to Python date object."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%d.%m.%Y").date()

async def import_data():
    """Import test data from CSV files into the database."""
    # Path to data files
    data_dir = Path("../test_data_for_DB")
    
    async for db in get_db():
        # Clear existing data
        await db.execute(text("DELETE FROM payments"))
        await db.execute(text("DELETE FROM credits"))
        await db.execute(text("DELETE FROM plans"))
        await db.execute(text("DELETE FROM dictionary"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()
        
        print("Importing dictionary data...")
        with open(data_dir / "dictionary.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                dictionary = Dictionary(
                    id=int(row["id"]),
                    name=row["name"]
                )
                db.add(dictionary)
        await db.commit()
        
        print("Importing user data...")
        with open(data_dir / "users.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                user = User(
                    id=int(row["id"]),
                    login=row["login"],
                    # Use a default password for all imported users
                    password=get_password_hash("password123"),
                    registration_date=parse_date(row["registration_date"])
                )
                db.add(user)
        await db.commit()
        
        print("Importing credit data...")
        with open(data_dir / "credits.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                credit = Credit(
                    id=int(row["id"]),
                    user_id=int(row["user_id"]),
                    issuance_date=parse_date(row["issuance_date"]),
                    return_date=parse_date(row["return_date"]),
                    actual_return_date=parse_date(row["actual_return_date"]),
                    body=Decimal(row["body"]),
                    percent=Decimal(row["percent"])
                )
                db.add(credit)
        await db.commit()
        
        print("Importing payment data...")
        with open(data_dir / "payments.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            batch_size = 1000
            batch = []
            
            for i, row in enumerate(reader):
                payment = Payment(
                    id=int(row["id"]),
                    credit_id=int(row["credit_id"]),
                    payment_date=parse_date(row["payment_date"]),
                    type_id=int(row["type_id"]),
                    sum=Decimal(row["sum"])
                )
                batch.append(payment)
                
                # Process in batches to avoid memory issues
                if len(batch) >= batch_size:
                    db.add_all(batch)
                    await db.commit()
                    batch = []
                    print(f"Imported {i+1} payments...")
            
            # Add remaining payments
            if batch:
                db.add_all(batch)
                await db.commit()
        
        print("Importing plan data...")
        with open(data_dir / "plans.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                plan = Plan(
                    id=int(row["id"]),
                    period=parse_date(row["period"]),
                    sum=Decimal(row["sum"]),
                    category_id=int(row["category_id"])
                )
                db.add(plan)
        await db.commit()
        
        print("Data import completed successfully!")

if __name__ == "__main__":
    asyncio.run(import_data()) 