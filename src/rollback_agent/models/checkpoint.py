"""Data models for checkpoint system."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid
from zoneinfo import ZoneInfo

@dataclass
class Checkpoint:
    """Represents a checkpoint in the conversation."""
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(ZoneInfo('Asia/Shanghai')))
    checkpoint_type: str = "manual"  # manual, auto, error
    name: Optional[str] = None
    message_count: int = 0
    conversation_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    session_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for storage."""
        from ..utils.time_utils import format_datetime
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": format_datetime(self.timestamp),
            "checkpoint_type": self.checkpoint_type,
            "name": self.name,
            "message_count": self.message_count,
            "conversation_snapshot": self.conversation_snapshot,
            "session_state": self.session_state,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        if isinstance(data.get("timestamp"), str):
            from ..utils.time_utils import parse_datetime
            data = dict(data)
            data["timestamp"] = parse_datetime(data["timestamp"]) 
        return cls(**data)
