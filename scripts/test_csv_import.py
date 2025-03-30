"""Test script for importing plans from CSV."""

import asyncio
import io
import traceback
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.init_db import get_db
from components.plan.repository import PlanRepository

async def test_csv_import():
    """Test importing plans from CSV file."""
    try:
        # Path to CSV file
        csv_path = Path("test_data_for_DB/plans.csv")
        
        if not csv_path.exists():
            print(f"Error: File not found at {csv_path}")
            return
        
        print(f"Reading file: {csv_path}")
        # Read CSV file
        with open(csv_path, "rb") as f:
            file_content = f.read()
        
        print(f"File content length: {len(file_content)} bytes")
        
        async for db in get_db():
            # Initialize repository
            repo = PlanRepository(db)
            
            print("Starting CSV import test...")
            # Test CSV import
            try:
                success, message, errors = await repo.upload_plans_from_csv(io.BytesIO(file_content))
                
                print(f"Success: {success}")
                print(f"Message: {message}")
                
                if errors:
                    print("Errors:")
                    for error in errors:
                        print(f"  Row {error['row']}: {error['message']}")
            except Exception as e:
                print(f"Exception during import: {e}")
                traceback.print_exc()
            
            break  # Only need one session
    except Exception as e:
        print(f"Test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_csv_import()) 