"""
Database Initialization Script
"""
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base, SessionLocal
from app.models import *
from app.services.auth_service import AuthService


def init_database():
    """Initialize database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    print("\nInitializing default data...")
    db = SessionLocal()
    try:
        AuthService.init_default_data(db)
        print("Default data initialized successfully!")
        print("\nDefault login credentials:")
        print("  Username: admin")
        print("  Password: admin123")
    except Exception as e:
        print(f"Failed to initialize default data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
