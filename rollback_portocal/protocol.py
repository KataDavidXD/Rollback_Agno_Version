from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# Tools that act as logical checkpoints and do not require reverse handlers.
# Example names can be adapted by the integrator.
CHECKPOINT_TOOL_NAMES: Tuple[str, ...] = (
    # Generic names
    "save_checkpoint",
    "checkpoint",
    # Agent-specific checkpoint tool names (must not require reverse)
    "create_checkpoint_tool",
    "list_checkpoints_tool",
    "rollback_to_checkpoint_tool",
    "delete_checkpoint_tool",
    "get_checkpoint_info_tool",
    "cleanup_auto_checkpoints_tool",
)


# Callable signatures for forward and reverse tool handlers
ForwardTool = Callable[[Mapping[str, Any]], Any]
ReverseTool = Callable[[Mapping[str, Any], Any], Any]


@dataclass(frozen=True)
class ToolSpec:
    """Specification for a tool with optional reverse tool.

    A reverse tool is required unless the tool's name is in CHECKPOINT_TOOL_NAMES.
    The reverse tool receives the original args and the forward result.
    """

    name: str
    forward: ForwardTool
    reverse: Optional[ReverseTool] = None

    def validate(self) -> None:
        if self.name not in CHECKPOINT_TOOL_NAMES and self.reverse is None:
            raise ValueError(
                f"Tool '{self.name}' must register a reverse handler unless it is a checkpoint tool."
            )


@dataclass
class ToolInvocationRecord:
    """A single tool invocation captured for rollback/redo."""

    tool_name: str
    args: Dict[str, Any]
    result: Any
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


@dataclass
class ReverseInvocationResult:
    """Result of invoking a reverse tool during rollback."""

    tool_name: str
    reversed_successfully: bool
    error_message: Optional[str] = None


