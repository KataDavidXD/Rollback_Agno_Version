"""User authentication and management module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class User:
    """User model for authentication and authorization.
    
    This class represents a user in the Rollback Agent System with
    authentication capabilities and admin privileges support.
    
    Attributes:
        id: Unique identifier for the user in the database.
        username: Unique username for authentication.
        password_hash: SHA256 hashed password for security.
        is_admin: Flag indicating admin privileges (only rootusr by default).
        created_at: Timestamp when the user was created.
        last_login: Timestamp of the user's last login.
    
    Example:
        >>> user = User(username="john_doe")
        >>> user.set_password("secure_password")
        >>> user.verify_password("secure_password")
        True
        >>> user.to_dict()
        {'id': None, 'username': 'john_doe', 'is_admin': False, ...}
    """
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA256.
        
        Args:
            password: Plain text password to hash.
            
        Returns:
            Hexadecimal string representation of the SHA256 hash.
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify.
            
        Returns:
            True if password matches, False otherwise.
        """
        return self.password_hash == self.hash_password(password)
    
    def set_password(self, password: str):
        """Set a new password for the user.
        
        Args:
            password: New plain text password to set.
        """
        self.password_hash = self.hash_password(password)
    
    def to_dict(self):
        """Convert user object to dictionary.
        
        Returns:
            Dictionary representation of the user (excludes password_hash).
        """
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create a User instance from a dictionary.
        
        Args:
            data: Dictionary containing user data.
            
        Returns:
            User instance populated with the provided data.
        """
        user = cls()
        user.id = data.get("id")
        user.username = data.get("username", "")
        user.password_hash = data.get("password_hash", "")
        user.is_admin = data.get("is_admin", False)
        
        if data.get("created_at"):
            user.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_login"):
            user.last_login = datetime.fromisoformat(data["last_login"])
        
        return user