"""
Database initialization - creates all tables.
Run this once before starting the application.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base, engine
from sqlalchemy import text


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def reset_db():
    """Drop all tables and recreate them (development only)."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "init"
    if action == "reset":
        reset_db()
    else:
        init_db()
