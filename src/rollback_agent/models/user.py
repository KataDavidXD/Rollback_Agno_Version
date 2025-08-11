"""User model for authentication."""
from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Optional
from zoneinfo import ZoneInfo
from ..utils.time_utils import parse_datetime, format_datetime

@dataclass  
class User:
    """User model for the rollback agent."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return self.password_hash == self.hash_password(password)

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password_hash": self.password_hash,
            "created_at": format_datetime(self.created_at) if self.created_at else None,
            "last_login": format_datetime(self.last_login) if self.last_login else None
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "User":
        """Create User from database row."""
        return cls(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            created_at=parse_datetime(row[3]) if row[3] else None,
            last_login=parse_datetime(row[4]) if row[4] else None
        )