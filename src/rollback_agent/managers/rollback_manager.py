"""Rollback operations manager."""
from typing import Dict, List, Any, Optional
from ..agent import create_rollback_agent
from ..utils.serialization import serialize_datetimes


class RollbackManager:
    """Handles rollback operations and state restoration."""

    @staticmethod
    def handle_rollback(agent, current_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Check and handle rollback if requested.
        
        Returns:
            Dict with new agent and rollback info if rollback occurred, None otherwise
        """
        if not agent.session_state.get("rollback_completed"):
            return None

        # Save rollback information
        new_session_id = agent.session_state.get("new_session_id", "rollback_session")
        conversation_to_restore = agent.session_state.get("rollback_conversation", [])
        old_session_state = agent.session_state.copy()
        old_session_id = agent.session_id

        # Create new agent with new session
        new_agent = create_rollback_agent(
            session_id=new_session_id,
            user_id=str(current_user_id)
        )

        # Store metadata
        new_agent.session_state["current_user_id"] = current_user_id
        new_agent.session_state["parent_session_id"] = old_session_id
        new_agent.session_state["needs_parent_update"] = True

        # Restore session state from old agent (excluding rollback flags)
        for key, value in old_session_state.items():
            if key not in ["rollback_completed", "rollback_conversation", "new_session_id"]:
                new_agent.session_state[key] = serialize_datetimes(value)

        # Process conversation context
        context = RollbackManager.process_conversation_context(conversation_to_restore)
        new_agent.session_state["restored_conversation_context"] = context

        return {
            "agent": new_agent,
            "new_session_id": new_session_id,
            "conversation_restored": len(conversation_to_restore),
            "context": context,
            "old_session_id": old_session_id
        }

    @staticmethod
    def process_conversation_context(conversation: List[Dict]) -> str:
        """Process conversation history into context string."""
        if not conversation:
            return ""

        context_lines = ["Previous conversation before rollback:"]
        for msg in conversation:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            if role != "System":  # Skip system messages for context
                context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)

    @staticmethod
    def display_rollback_summary(rollback_info: Dict[str, Any]):
        """Display rollback completion summary."""
        print("\n🔄 Rollback detected. Completing rollback immediately...")

        if rollback_info.get("context"):
            print("\n--- Restored Conversation History ---")
            for line in rollback_info["context"].split("\n")[1:]:  # Skip header line
                print(line)
            print("--- End of Restored History ---\n")

        print(f"✅ Rollback completed! Now using session: {rollback_info['new_session_id']}")
        print(f"📜 Restored {rollback_info['conversation_restored']} messages from checkpoint")
        print("You can continue the conversation from the checkpoint.\n")
