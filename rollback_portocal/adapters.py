from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

try:
    # Optional import: only needed if using Agno toolkits
    from agno.agent import Toolkit  # type: ignore
except Exception:  # pragma: no cover - when agno is not available in env
    Toolkit = object  # Fallback to allow type annotations

from .protocol import CHECKPOINT_TOOL_NAMES, ToolSpec
from .registry import ToolRollbackRegistry


class AgnoToolkitAdapter:
    """Adapter to register and execute Agno Toolkit tools with rollback tracking.

    This does not depend on internal Agno mechanics. It treats `Toolkit` as an
    object with callables named by the tool names. Users must provide:
    - tool_names: list of forward tool names to expose
    - reverse_map: mapping of tool_name -> reverse callable
      (reverse is required unless tool_name in CHECKPOINT_TOOL_NAMES)
    """

    def __init__(self, toolkit: Toolkit, registry: Optional[ToolRollbackRegistry] = None) -> None:
        self.toolkit = toolkit
        self.registry = registry or ToolRollbackRegistry()

    def register_tools(
        self,
        tool_names: Sequence[str],
        reverse_map: Mapping[str, Callable[[Mapping[str, Any], Any], Any]],
    ) -> None:
        for name in tool_names:
            forward = getattr(self.toolkit, name, None)
            if not callable(forward):
                raise AttributeError(f"Toolkit has no callable tool '{name}'")

            reverse = reverse_map.get(name)
            if name in CHECKPOINT_TOOL_NAMES:
                reverse = None

            self.registry.register_tool(ToolSpec(name=name, forward=forward, reverse=reverse))

    def execute_and_record(self, tool_name: str, args: Mapping[str, Any]) -> Any:
        spec = self.registry.get_tool(tool_name)
        if not spec:
            raise ValueError(f"Tool '{tool_name}' is not registered in rollback registry")

        try:
            result = spec.forward(args)
            self.registry.record_invocation(tool_name, args, result, success=True)
            return result
        except Exception as e:
            self.registry.record_invocation(tool_name, args, None, success=False, error_message=str(e))
            raise


