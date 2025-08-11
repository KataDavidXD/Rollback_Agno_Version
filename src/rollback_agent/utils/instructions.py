"""Instruction resources and builders for the rollback agent.

Separates checkpoint-related defaults/context from tool-specific instruction
extensions so they can be managed independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class InstructionContext:
    """Holds dynamic values used to render instruction text.

    - Checkpoint settings are treated as the default/base instruction content
      and loaded regardless of what tools are enabled.
    - Tool-specific guidance (e.g., Baidu) is appended conditionally.
    """

    auto_checkpoint_interval: int
    max_checkpoints: int
    message_counter: int
    checkpoints: List[str]
    restored_conversation_context: str = ""


def get_checkpoint_instructions() -> List[str]:
    """Static guidance about checkpoint and rollback behavior."""
    return [
        "You are an AI assistant with checkpoint and rollback capabilities.",
        "You can:",
        "- Create checkpoints to save the current conversation state",
        "- List all available checkpoints",
        "- Rollback to a previous checkpoint (restores state and removes newer checkpoints)",
        "- Delete checkpoints that are no longer needed",
    ]


def get_checkpoint_context_lines(ctx: InstructionContext) -> List[str]:
    """Dynamic context describing current checkpoint configuration and state."""
    lines: List[str] = [
        "Current checkpoint configuration:",
        f"- Auto checkpoint interval: {ctx.auto_checkpoint_interval} messages",
        f"- Maximum checkpoints: {ctx.max_checkpoints}",
        f"- Current message count: {ctx.message_counter}",
        f"Available checkpoints: {ctx.checkpoints}",
    ]
    if ctx.restored_conversation_context:
        lines.append(ctx.restored_conversation_context)
    return lines


def get_baidu_search_instructions() -> List[str]:
    """Guidance for Baidu search usage per Agno example docs."""
    return [
        "Baidu search usage guidelines:",
        "- Given a topic by the user, respond with the 3 most relevant search results about that topic",
        "- Search for 5 results and select the top 3 unique items",
        "- Search in both English and Chinese",
    ]


def compose_instructions(ctx: InstructionContext, *, include_baidu_search: bool = False) -> List[str]:
    """Compose the full instruction list, separating checkpoint defaults from tool extensions."""
    instructions: List[str] = []
    # Base: checkpoint defaults and dynamic context
    instructions.extend(get_checkpoint_instructions())
    instructions.extend(get_checkpoint_context_lines(ctx))

    # Tool extensions
    if include_baidu_search:
        instructions.extend(get_baidu_search_instructions())

    return instructions


