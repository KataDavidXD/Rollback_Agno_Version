"""User repository for database operations.

Provides ORM functionality for User entities with SQLite backend.
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from src.auth.user import User
from src.database.db_config import get_database_path


class UserRepository:
    """Repository for User CRUD operations with SQLite.
    
    This class handles all database operations for User entities,
    including automatic initialization of the database schema and
    creation of the default admin user (rootusr).
    
    Attributes:
        db_path: Path to the SQLite database file.
    
    Example:
        >>> repo = UserRepository()
        >>> user = User(username="alice")
        >>> user.set_password("secret")
        >>> saved_user = repo.save(user)
        >>> found_user = repo.find_by_username("alice")
        >>> found_user.verify_password("secret")
        True
    """
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the user repository.
        
        Args:
            db_path: Path to SQLite database file. If None, uses configured default.
        """
        self.db_path = db_path or get_database_path()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema and create default admin user.
        
        Creates the users table if it doesn't exist and ensures
        the rootusr admin account is present with default password "1234".
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT,
                    last_login TEXT,
                    data TEXT
                )
            """)
            
            cursor.execute("""
                SELECT COUNT(*) FROM users WHERE username = 'rootusr'
            """)
            if cursor.fetchone()[0] == 0:
                root_user = User(
                    username="rootusr",
                    is_admin=True,
                    created_at=datetime.now()
                )
                root_user.set_password("1234")
                self.save(root_user)
            
            conn.commit()
    
    def save(self, user: User) -> User:
        """Save or update a user in the database.
        
        Performs insert if user.id is None, otherwise updates existing record.
        Stores both structured fields and full JSON representation for flexibility.
        
        Args:
            user: User object to save.
            
        Returns:
            The saved User object with id populated if newly created.
            
        Note:
            Password hash is stored separately from the JSON data for security.
        """
        user_dict = user.to_dict()
        user_dict['password_hash'] = user.password_hash
        json_data = json.dumps(user_dict)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user.id is None:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, is_admin, created_at, last_login, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.username,
                    user.password_hash,
                    1 if user.is_admin else 0,
                    user.created_at.isoformat() if user.created_at else None,
                    user.last_login.isoformat() if user.last_login else None,
                    json_data
                ))
                user.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE users 
                    SET username = ?, password_hash = ?, is_admin = ?, 
                        created_at = ?, last_login = ?, data = ?
                    WHERE id = ?
                """, (
                    user.username,
                    user.password_hash,
                    1 if user.is_admin else 0,
                    user.created_at.isoformat() if user.created_at else None,
                    user.last_login.isoformat() if user.last_login else None,
                    json_data,
                    user.id
                ))
            
            conn.commit()
        
        return user
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by their database ID.
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            User object if found, None otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, is_admin, created_at, last_login, data
                FROM users WHERE id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
        
        return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their username.
        
        Args:
            username: The username to search for.
            
        Returns:
            User object if found, None otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, is_admin, created_at, last_login, data
                FROM users WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
        
        return None
    
    def find_all(self) -> List[User]:
        """Retrieve all users from the database.
        
        Returns:
            List of all User objects in the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, is_admin, created_at, last_login, data
                FROM users
            """)
            
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
    
    def delete(self, user_id: int) -> bool:
        """Delete a user from the database.
        
        Args:
            user_id: The ID of the user to delete.
            
        Returns:
            True if a user was deleted, False if no user found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def _row_to_user(self, row) -> User:
        """Convert a database row to a User object.
        
        Args:
            row: Tuple containing database fields (id, username, password_hash,
                 is_admin, created_at, last_login, json_data).
            
        Returns:
            User object reconstructed from database data.
            
        Note:
            Prioritizes JSON data if available, falls back to individual fields.
        """
        user_id, username, password_hash, is_admin, created_at, last_login, json_data = row
        
        if json_data:
            user_dict = json.loads(json_data)
        else:
            user_dict = {
                "id": user_id,
                "username": username,
                "is_admin": bool(is_admin),
                "created_at": created_at,
                "last_login": last_login
            }
        
        user_dict["password_hash"] = password_hash
        
        user = User.from_dict(user_dict)
        user.id = user_id
        
        return user