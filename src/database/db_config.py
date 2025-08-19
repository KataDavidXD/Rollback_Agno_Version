"""Database configuration and initialization module.

Provides centralized database path management and ensures database file exists.
"""

import os
from pathlib import Path
from typing import Optional


class DatabaseConfig:
    """Database configuration and path management.
    
    Ensures database directory and file exist, but does not create tables.
    Table creation is handled by individual repository classes.
    
    Attributes:
        db_path: Path to the SQLite database file.
    
    Example:
        >>> from src.database.db_config import get_database_path
        >>> db_path = get_database_path()
        >>> # Use db_path in repository classes
    """
    
    DEFAULT_DB_PATH = "data/rollback.db"
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database configuration.
        
        Args:
            db_path: Custom database path. If None, uses DEFAULT_DB_PATH.
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database directory and file exist."""
        # Create directory if needed
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        
        # Create empty database file if it doesn't exist
        if not os.path.exists(self.db_path):
            Path(self.db_path).touch()
            print(f"Created database file: {self.db_path}")
    
    def get_path(self) -> str:
        """Get the database file path.
        
        Returns:
            The path to the database file.
        """
        return self.db_path


# Singleton instance for shared database path
_db_config = DatabaseConfig()


def get_database_path() -> str:
    """Get the configured database path.
    
    Returns:
        Path to the database file.
    """
    return _db_config.get_path()


def set_database_path(db_path: str):
    """Set a custom database path.
    
    Args:
        db_path: New database path to use.
    """
    global _db_config
    _db_config = DatabaseConfig(db_path)