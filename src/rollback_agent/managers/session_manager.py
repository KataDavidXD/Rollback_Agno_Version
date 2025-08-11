"""Session management for rollback agent."""
from typing import Optional, Dict, Any
from datetime import datetime
from ..utils.database import get_db_connection
from ..agent import create_rollback_agent


class SessionManager:
    """Manages agent sessions and their lifecycle."""

    def __init__(self, db_file: str = "data/rollback_agent.db"):
        self.db_file = db_file

    def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_name: Optional[str] = None,
        **agent_kwargs
    ):
        """Create a new session with an agent."""
        agent = create_rollback_agent(
            session_id=session_id,
            user_id=user_id,
            db_file=self.db_file,
            **agent_kwargs
        )

        if session_name:
            self.update_session_name(agent.session_id, session_name)

        return agent

    def update_session_activity(self, session_id: str, user_id: int):
        """Update last activity timestamp for a session."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE rollback_sessions 
                SET last_activity = CURRENT_TIMESTAMP,
                    user_id = ?
                WHERE session_id = ?
            """, (user_id, session_id))
            conn.commit()
        finally:
            conn.close()

    def update_session_name(self, session_id: str, session_name: str):
        """Update session name."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE rollback_sessions 
                SET session_name = ?
                WHERE session_id = ?
            """, (session_name, session_id))
            conn.commit()
        finally:
            conn.close()

    def update_parent_session(self, session_id: str, parent_session_id: str):
        """Update parent session reference after rollback."""
        conn = get_db_connection(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE rollback_sessions 
                SET parent_session_id = ?,
                    session_name = ?
                WHERE session_id = ?
            """, (
                parent_session_id,
                f"Rollback from {parent_session_id[:8]}",
                session_id
            ))
            conn.commit()
        finally:
            conn.close()
