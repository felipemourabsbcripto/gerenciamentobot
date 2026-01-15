"""
Database package initialization.
"""
from src.database.database import Database, db
from src.database.repositories import UserRepository, AssetRepository, AlertRepository, EntryRepository, AdminRepository


def get_async_session():
    """Get a database session context manager."""
    return db.get_session()


__all__ = [
    "Database", 
    "db", 
    "get_async_session",
    "UserRepository", 
    "AssetRepository", 
    "AlertRepository", 
    "EntryRepository",
    "AdminRepository"
]
