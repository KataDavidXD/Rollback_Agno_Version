"""Checkpoint management tools for the rollback agent."""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from agno.agent import Agent
from ..models.checkpoint import Checkpoint
from ..utils.serialization import serialize_datetimes
from ..utils.time_utils import now, format_datetime


def create_checkpoint(
    agent: Agent,
    name: Optional[str] = None,
    checkpoint_type: str = "manual"
) -> str:
    """
    Create a checkpoint of the current conversation state.
    
    Args:
        agent: The Agno agent instance
        name: Optional name for the checkpoint
        checkpoint_type: Type of checkpoint (manual, auto, error)
    
    Returns:
        Success message with checkpoint ID
    """
    try:
        messages = agent.get_messages_for_session()
        # Convert messages to serializable format
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": getattr(msg, 'timestamp', None).isoformat() if hasattr(msg, 'timestamp') and getattr(msg, 'timestamp') else None
            }
            for msg in messages
        ] if messages else []
    except Exception as e:
        # Log error if needed, fallback to empty history
        conversation_history = []
    # Create checkpoint instance
    checkpoint = Checkpoint(
        name=name or f"Checkpoint at {format_datetime(now())}",
        checkpoint_type=checkpoint_type,
        message_count=agent.session_state.get("message_counter", 0),
        session_state=serialize_datetimes({k: v for k, v in agent.session_state.items() if k != "checkpoints"}),  # Copy current state
        conversation_snapshot=conversation_history,
        metadata={
            "created_by": "user" if checkpoint_type == "manual" else "system",
            "trigger": f"{checkpoint_type} checkpoint",
            "conversation_length": len(conversation_history),
            "user_id": agent.session_state.get("current_user_id")
        }
    )

    # Add to checkpoints list
    if "checkpoints" not in agent.session_state:
        agent.session_state["checkpoints"] = []

    # Maintain max checkpoints limit
    max_checkpoints = agent.session_state.get("max_checkpoints", 10)
    if len(agent.session_state["checkpoints"]) >= max_checkpoints:
        # Remove oldest checkpoint
        agent.session_state["checkpoints"].pop(0)

    # Add new checkpoint
    agent.session_state["checkpoints"].append(checkpoint.to_dict())

    return f"✅ Checkpoint created successfully!\nID: {checkpoint.checkpoint_id}\nName: {checkpoint.name}"


def list_checkpoints(agent: Agent) -> str:
    """
    List all available checkpoints.
    
    Args:
        agent: The Agno agent instance
    
    Returns:
        Formatted list of checkpoints
    """
    checkpoints = agent.session_state.get("checkpoints", [])

    if not checkpoints:
        return "No checkpoints available."

    result = "📋 Available Checkpoints:\n\n"
    for idx, cp_data in enumerate(checkpoints):
        cp = Checkpoint.from_dict(cp_data)
        result += f"{idx + 1}. {cp.name}\n"
        result += f"   ID: {cp.checkpoint_id[:8]}...\n"
        result += f"   Type: {cp.checkpoint_type}\n"
        result += f"   Created: {cp.timestamp.isoformat(timespec='seconds')}\n"
        result += f"   Messages: {cp.message_count}\n\n"

    return result


def delete_checkpoint(agent: Agent, checkpoint_id: str) -> str:
    """
    Delete a specific checkpoint.
    
    Args:
        agent: The Agno agent instance
        checkpoint_id: ID of the checkpoint to delete
    
    Returns:
        Success or error message
    """
    checkpoints = agent.session_state.get("checkpoints", [])

    # Find and remove checkpoint
    for idx, cp_data in enumerate(checkpoints):
        if cp_data["checkpoint_id"] == checkpoint_id or cp_data["checkpoint_id"].startswith(checkpoint_id):
            removed = checkpoints.pop(idx)
            agent.session_state["checkpoints"] = checkpoints
            return f"✅ Checkpoint '{removed['name']}' deleted successfully."

    return f"❌ Checkpoint with ID '{checkpoint_id}' not found."

def rollback_to_checkpoint(agent: Agent, checkpoint_id: str) -> str:
    """
    Rollback the conversation to a specific checkpoint.
    
    Args:
        agent: The Agno agent instance
        checkpoint_id: ID of the checkpoint to rollback to
    
    Returns:
        Success or error message
    """
    checkpoints = agent.session_state.get("checkpoints", [])
    
    # Find the checkpoint
    checkpoint_index = -1
    checkpoint_data = None
    
    for idx, cp_data in enumerate(checkpoints):
        if cp_data["checkpoint_id"] == checkpoint_id or cp_data["checkpoint_id"].startswith(checkpoint_id):
            checkpoint_index = idx
            checkpoint_data = cp_data
            break
    
    if checkpoint_data is None:
        return f"❌ Checkpoint with ID '{checkpoint_id}' not found."
    
    # Create checkpoint object from data
    checkpoint = Checkpoint.from_dict(checkpoint_data)
    
    # Restore the session state (excluding checkpoints)
    for key, value in checkpoint.session_state.items():
        if key != "checkpoints":
            agent.session_state[key] = value
    
    # Remove all checkpoints after this one
    agent.session_state["checkpoints"] = checkpoints[:checkpoint_index + 1]
    
    # Update message counter to checkpoint's message count
    agent.session_state["message_counter"] = checkpoint.message_count
    
    # Store the conversation snapshot in session state for the main loop to handle
    agent.session_state["rollback_conversation"] = checkpoint.conversation_snapshot
    agent.session_state["rollback_completed"] = True

    # Clear current session to prepare for restore
    if hasattr(agent, 'storage') and agent.storage and hasattr(agent, 'session_id'):
        try:
            # Create a new session ID for the rolled-back state
            new_session_id = f"{agent.session_id}_rollback_{checkpoint.checkpoint_id[:8]}"
            agent.session_state["new_session_id"] = new_session_id
        except:
            pass

    return (f"✅ Rollback prepared for checkpoint: {checkpoint.name}\n"
            f"Message count reset to: {checkpoint.message_count}\n"
            f"Conversation history will be restored to {len(checkpoint.conversation_snapshot)} messages\n"
            f"🔄 Rollback will complete immediately.")

