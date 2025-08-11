"""Main rollback agent configuration."""
import os
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from agno.agent import Agent
from agno.storage.sqlite import SqliteStorage
from agno.models.openai import OpenAIChat
from agno.tools.baidusearch import BaiduSearchTools
from agno.memory.v2 import Memory
from .tools.checkpoint import (
    create_checkpoint,
    list_checkpoints,
    delete_checkpoint,
    rollback_to_checkpoint,
)
from .utils.time_utils import now, format_datetime
from .utils.instructions import InstructionContext, compose_instructions

# Tool hook to auto-create a checkpoint after each tool call (excluding checkpoint tools themselves)
CHECKPOINT_TOOL_NAMES = {
    "create_checkpoint",
    "list_checkpoints",
    "delete_checkpoint",
    "rollback_to_checkpoint",
}


def auto_checkpoint_hook(
    agent: Agent, function_name: str, function_call: Callable, arguments: Dict[str, Any]
):
    """Post-call tool hook that creates a checkpoint after every tool call.

    Skips creating a checkpoint for checkpoint-management tools themselves to avoid noise.
    """
    # Perform the actual tool call first
    result = function_call(**arguments)

    # Skip creating checkpoints for checkpoint-related tools
    print(function_name)
    if function_name not in CHECKPOINT_TOOL_NAMES:
        print(f"Auto checkpoint after: {function_name}")
        try:
            checkpoint_name = f"Auto checkpoint after: {function_name}"
            create_checkpoint(agent=agent, name=checkpoint_name, checkpoint_type="auto")
            print(f"Auto checkpoint created: {checkpoint_name}")
        except Exception:
            # Silently ignore checkpoint creation failures; tool result should not be impacted
            pass

    return result


def create_rollback_agent(
    model_id: str = "gpt-4o-mini",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db_file: str = "data/rollback_agent.db",
    auto_checkpoint_interval: int = 5,
    max_checkpoints: int = 10
) -> Agent:
    """
    Create a rollback agent with checkpoint capabilities.
    
    Args:
        model_id: OpenAI model ID to use
        session_id: Session ID for the agent
        user_id: User ID for multi-user support
        db_file: Path to SQLite database file
        auto_checkpoint_interval: Number of messages between auto checkpoints
        max_checkpoints: Maximum number of checkpoints to maintain
    
    Returns:
        Configured Agent instance
    """
    # Initialize storage
    storage = SqliteStorage(
        table_name="rollback_sessions",
        db_file=db_file
    )

    def _sanitize_base_url(raw_url: Optional[str]) -> Optional[str]:
        if not raw_url:
            return None
        url = raw_url.strip().rstrip("/")
        if not url:
            return None
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        return url

    base_url_env = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
    base_url = _sanitize_base_url(base_url_env)
    api_key = os.getenv("OPENAI_API_KEY")

    # Build instruction context and compose instructions
    instruction_ctx = InstructionContext(
        auto_checkpoint_interval=auto_checkpoint_interval,
        max_checkpoints=max_checkpoints,
        message_counter=0,
        checkpoints=[],
        restored_conversation_context="",
    )
    initial_instructions = compose_instructions(
        instruction_ctx,
        include_baidu_search=True,
    )

    # Create the agent
    agent = Agent(
        model=OpenAIChat(
            id=model_id,
            base_url=base_url,
            api_key=api_key,
        ),
        session_id=session_id or f"rollback_session_{format_datetime(now())}",   
        user_id=user_id,
        memory=Memory(),
        storage=storage,
        session_state={
            "checkpoints": [],
            "message_counter": 0,
            "auto_checkpoint_interval": auto_checkpoint_interval,
            "max_checkpoints": max_checkpoints,
            "restored_conversation_context": ""
        },
        tools=[
            create_checkpoint,
            list_checkpoints,
            delete_checkpoint,
            rollback_to_checkpoint,
            BaiduSearchTools(),
        ],
        tool_hooks=[auto_checkpoint_hook],
        add_history_to_messages=True,
        num_history_runs=10,
        add_state_in_messages=True,
        instructions=initial_instructions,
        markdown=True,
    )
    return agent
