"""User management for authentication."""
import sqlite3
from datetime import datetime
from ..utils.time_utils import now
from typing import Optional, List, Tuple
from ..models.user import User
from ..utils.database import get_db_connection


class UserManager:
    """Manages user authentication and sessions."""

    def __init__(self, db_file: str = "data/rollback_agent.db"):
        self.db_file = db_file

    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Register new user.
        
        Returns:
            (success, message) tuple
        """
        if not username or not password:
            return False, "Username and password are required"

        if len(password) < 4:
            return False, "Password must be at least 4 characters"

        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()

        try:
            # Check if user already exists
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, f"Username '{username}' already exists"

            # Create new user
            password_hash = User.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            return True, f"User '{username}' registered successfully!"

        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()

    def login(self, username: str, password: str) -> Optional[User]:
        """
        Login user.
        
        Returns:
            User object if successful, None otherwise
        """
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            user = User.from_db_row(tuple(row))

            # Verify password
            if not user.verify_password(password):
                return None

            # Update last login
            self.update_last_login(user.user_id)
            user.last_login = now()

            return user

        finally:
            conn.close()

    def update_last_login(self, user_id: int):
        """Update last login timestamp."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def get_user_sessions(self, user_id: int) -> List[dict]:
        """Get all sessions for a user."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT session_id, session_name, created_at, last_activity, 
                       is_active, parent_session_id
                FROM rollback_sessions
                WHERE user_id = ?
                ORDER BY last_activity DESC
            """, (user_id,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row["session_id"],
                    "session_name": row["session_name"] or f"Session {row['session_id'][:40]}",
                    "created_at": row["created_at"],
                    "last_activity": row["last_activity"],
                    "is_active": bool(row["is_active"]),
                    "parent_session_id": row["parent_session_id"]
                })

            return sessions

        finally:
            conn.close()

    def get_pending_rollbacks(self, user_id: int) -> List[dict]:
        """Get all pending rollbacks for a user."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT rollback_id, original_session_id, checkpoint_data,
                       rollback_timestamp
                FROM rollback_states
                WHERE user_id = ? AND completed = FALSE
                ORDER BY rollback_timestamp DESC
            """, (user_id,))

            rollbacks = []
            for row in cursor.fetchall():
                rollbacks.append({
                    "rollback_id": row["rollback_id"],
                    "original_session_id": row["original_session_id"],
                    "checkpoint_data": row["checkpoint_data"],
                    "rollback_timestamp": row["rollback_timestamp"]
                })

            return rollbacks

        finally:
            conn.close()
