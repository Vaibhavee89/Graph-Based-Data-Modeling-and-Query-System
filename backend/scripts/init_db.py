"""Initialize database tables."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, engine
from app.models import *  # Import all models


def main():
    """Create all database tables."""
    print("Creating database tables...")
    init_db()
    print("✓ Database tables created successfully!")

    # Print table names
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nCreated {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")


if __name__ == "__main__":
    main()
