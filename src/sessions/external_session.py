"""External session model for the rollback agent system.

Represents user-visible sessions that contain multiple internal Agno sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class ExternalSession:
    """External session model visible to users.
    
    External sessions are the main conversation containers that users interact with.
    Each external session can contain multiple internal Agno sessions created during
    rollback operations.
    
    Attributes:
        id: Unique identifier for the session.
        user_id: ID of the user who owns this session.
        session_name: User-friendly name for the session.
        created_at: When the session was created.
        updated_at: When the session was last updated.
        is_active: Whether the session is currently active.
        internal_session_ids: List of Agno session IDs associated with this external session.
        current_internal_session_id: The currently active internal Agno session ID.
    
    Example:
        >>> session = ExternalSession(
        ...     user_id=1,
        ...     session_name="Project Discussion",
        ...     created_at=datetime.now()
        ... )
        >>> session.add_internal_session("agno_session_123")
    """
    
    id: Optional[int] = None
    user_id: int = 0
    session_name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    internal_session_ids: List[str] = field(default_factory=list)
    current_internal_session_id: Optional[str] = None
    
    def add_internal_session(self, agno_session_id: str):
        """Add a new internal Agno session ID to this external session.
        
        Args:
            agno_session_id: The Agno session ID to add.
        """
        if agno_session_id not in self.internal_session_ids:
            self.internal_session_ids.append(agno_session_id)
            self.current_internal_session_id = agno_session_id
    
    def set_current_internal_session(self, agno_session_id: str) -> bool:
        """Set the current active internal session.
        
        Args:
            agno_session_id: The Agno session ID to set as current.
            
        Returns:
            True if the session ID exists and was set, False otherwise.
        """
        if agno_session_id in self.internal_session_ids:
            self.current_internal_session_id = agno_session_id
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convert session to dictionary representation.
        
        Returns:
            Dictionary with session data.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_name": self.session_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "internal_session_ids": self.internal_session_ids,
            "current_internal_session_id": self.current_internal_session_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExternalSession":
        """Create an ExternalSession from dictionary data.
        
        Args:
            data: Dictionary containing session data.
            
        Returns:
            ExternalSession instance.
        """
        session = cls()
        session.id = data.get("id")
        session.user_id = data.get("user_id", 0)
        session.session_name = data.get("session_name", "")
        session.is_active = data.get("is_active", True)
        session.internal_session_ids = data.get("internal_session_ids", [])
        session.current_internal_session_id = data.get("current_internal_session_id")
        
        if data.get("created_at"):
            session.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            session.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return session