#!/usr/bin/env python3

from app.database import engine
from app.models import Base

def init_database():
    """Create all tables in the database"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
