"""Internal Agno session model for the rollback agent system.

Represents the actual Agno agent sessions within an external session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
import json


@dataclass
class InternalSession:
    """Internal Agno session model.
    
    Represents an actual Agno agent session that runs within an external session.
    Stores the session state and conversation history separately as per Agno's design.
    
    Attributes:
        id: Unique identifier for the internal session.
        external_session_id: ID of the parent external session.
        agno_session_id: The actual Agno session ID used by the agent.
        session_state: The agent's session state dictionary.
        conversation_history: List of conversation messages.
        created_at: When this internal session was created.
        is_current: Whether this is the current active session.
        checkpoint_count: Number of checkpoints created from this session.
    
    Example:
        >>> session = InternalSession(
        ...     external_session_id=1,
        ...     agno_session_id="agno_abc123",
        ...     session_state={"counter": 0}
        ... )
    """
    
    id: Optional[int] = None
    external_session_id: int = 0
    agno_session_id: str = ""
    session_state: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    is_current: bool = True
    checkpoint_count: int = 0
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user, assistant, system).
            content: The message content.
            **kwargs: Additional message metadata.
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.conversation_history.append(message)
    
    def update_state(self, new_state: Dict[str, Any]):
        """Update the session state.
        
        Args:
            new_state: Dictionary with state updates.
        """
        self.session_state.update(new_state)
    
    def to_dict(self) -> dict:
        """Convert internal session to dictionary representation.
        
        Returns:
            Dictionary with session data.
        """
        return {
            "id": self.id,
            "external_session_id": self.external_session_id,
            "agno_session_id": self.agno_session_id,
            "session_state": self.session_state,
            "conversation_history": self.conversation_history,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_current": self.is_current,
            "checkpoint_count": self.checkpoint_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "InternalSession":
        """Create an InternalSession from dictionary data.
        
        Args:
            data: Dictionary containing session data.
            
        Returns:
            InternalSession instance.
        """
        session = cls()
        session.id = data.get("id")
        session.external_session_id = data.get("external_session_id", 0)
        session.agno_session_id = data.get("agno_session_id", "")
        session.session_state = data.get("session_state", {})
        session.conversation_history = data.get("conversation_history", [])
        session.is_current = data.get("is_current", True)
        session.checkpoint_count = data.get("checkpoint_count", 0)
        
        if data.get("created_at"):
            session.created_at = datetime.fromisoformat(data["created_at"])
        
        return session