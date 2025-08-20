from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

from .protocol import (
    CHECKPOINT_TOOL_NAMES,
    ReverseInvocationResult,
    ToolInvocationRecord,
    ToolSpec,
)


class ToolRollbackRegistry:
    """Registry that enforces reverse tool registration and supports rollback/redo.

    Typical usage:
        registry = ToolRollbackRegistry()
        registry.register_tool(ToolSpec(name="create_file", forward=create_file, reverse=delete_file))

        # When executing a tool in your system, record the call:
        result = create_file({"path": "a.txt"})
        registry.record_invocation("create_file", {"path": "a.txt"}, result, success=True)

        # To rollback, it will call the reverse tools in reverse order:
        registry.rollback()

        # To redo, it will re-run forward tools in original order:
        registry.redo()
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}
        self._track: List[ToolInvocationRecord] = []

    # Registration
    def register_tool(self, spec: ToolSpec) -> None:
        spec.validate()
        self._tools[spec.name] = spec

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    # Tracking
    def record_invocation(
        self,
        tool_name: str,
        args: Mapping[str, Any],
        result: Any,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        record = ToolInvocationRecord(
            tool_name=tool_name,
            args=dict(args),
            result=result,
            success=success,
            error_message=error_message,
        )
        self._track.append(record)

    def clear_track(self) -> None:
        self._track.clear()

    def get_track(self) -> List[ToolInvocationRecord]:
        return list(self._track)

    # Rollback and redo operations
    def rollback(self) -> List[ReverseInvocationResult]:
        """Invoke reverse tools for all reversible records in reverse order.

        Records for tools listed in CHECKPOINT_TOOL_NAMES are skipped.
        If a tool has no reverse registered (should not happen due to validation), it is skipped.
        """
        results: List[ReverseInvocationResult] = []
        print("debug_mode: tool history:",self._track)
        for record in reversed(self._track):
            tool_name = record.tool_name
            if tool_name in CHECKPOINT_TOOL_NAMES:
                continue

            spec = self._tools.get(tool_name)
            if not spec or spec.reverse is None:
                # Non-reversible; skip
                results.append(
                    ReverseInvocationResult(
                        tool_name=tool_name,
                        reversed_successfully=False,
                        error_message="No reverse handler registered",
                    )
                )
                continue

            try:
                spec.reverse(record.args, record.result)
                results.append(
                    ReverseInvocationResult(
                        tool_name=tool_name,
                        reversed_successfully=True,
                    )
                )
            except Exception as e:
                results.append(
                    ReverseInvocationResult(
                        tool_name=tool_name,
                        reversed_successfully=False,
                        error_message=str(e),
                    )
                )

        return results

    def redo(self) -> List[ToolInvocationRecord]:
        """Re-execute forward tools in original order using recorded arguments.

        The results are appended to the track as new records. Checkpoint tools are
        re-executed like any other tool.
        """
        new_records: List[ToolInvocationRecord] = []
        for record in list(self._track):
            spec = self._tools.get(record.tool_name)
            if not spec:
                continue
            try:
                new_result = spec.forward(record.args)
                new_record = ToolInvocationRecord(
                    tool_name=record.tool_name,
                    args=dict(record.args),
                    result=new_result,
                    success=True,
                )
                self._track.append(new_record)
                new_records.append(new_record)
            except Exception as e:
                new_record = ToolInvocationRecord(
                    tool_name=record.tool_name,
                    args=dict(record.args),
                    result=None,
                    success=False,
                    error_message=str(e),
                )
                self._track.append(new_record)
                new_records.append(new_record)

        return new_records


