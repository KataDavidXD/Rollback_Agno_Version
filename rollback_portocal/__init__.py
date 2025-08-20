"""Rollback protocol for tool operations.

This module defines a simple protocol and registry to:
- Require a reverse tool when registering a tool (except checkpoint tools)
- Track tool invocations as a reproducible "track"
- Roll back by invoking reverse tools in reverse order
- Re-do by replaying the track in order

The registry is independent of the underlying agent/toolkit runtime,
so it can be integrated by recording tool calls at the integration points
available in your application (e.g., around tool execution).
"""

from .protocol import (
    CHECKPOINT_TOOL_NAMES,
    ToolInvocationRecord,
    ToolSpec,
    ReverseInvocationResult,
)
from .registry import ToolRollbackRegistry
from .adapters import AgnoToolkitAdapter

__all__ = [
    "CHECKPOINT_TOOL_NAMES",
    "ToolInvocationRecord",
    "ToolSpec",
    "ReverseInvocationResult",
    "ToolRollbackRegistry",
    "AgnoToolkitAdapter",
]


