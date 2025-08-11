
"""Conversation loop management."""
from typing import Optional, Callable
from .session_manager import SessionManager
from .rollback_manager import RollbackManager


class ConversationManager:
    """Manages the conversation loop and interactions."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.rollback_manager = RollbackManager()

    def run_conversation(
        self,
        agent,
        current_user,
        on_exit: Optional[Callable] = None,
        on_rollback: Optional[Callable] = None
    ):
        """
        Run the main conversation loop.
        
        Args:
            agent: The rollback agent instance
            current_user: Current user object
            on_exit: Callback when exiting conversation
            on_rollback: Callback when rollback occurs
        
        Returns:
            Final agent instance
        """
        print(f"\n🤖 Session Started: {agent.session_id}")
        print("Commands: 'create checkpoint', 'list checkpoints', 'rollback', 'quit'\n")

        agent.session_state["current_user_id"] = current_user.user_id

        while True:
            user_input = input("You: ")

            # Check for exit
            if user_input.lower() in ['quit', 'exit']:
                if on_exit:
                    on_exit(agent, current_user)
                else:
                    self._default_exit_handler(agent, current_user)
                break

            # Process user input
            response = agent.run(user_input, user_id=str(current_user.user_id))
            print(f"\nAgent: {response.content}\n")

            # Handle first run after rollback
            if agent.session_state.get("needs_parent_update"):
                self.session_manager.update_parent_session(
                    agent.session_id,
                    agent.session_state.get("parent_session_id")
                )
                agent.session_state.pop("needs_parent_update", None)

            # Update counters and activity
            agent.session_state["message_counter"] += 1
            self.session_manager.update_session_activity(
                agent.session_id,
                current_user.user_id
            )

            # Check for rollback
            rollback_info = self.rollback_manager.handle_rollback(
                agent,
                current_user.user_id
            )

            if rollback_info:
                if on_rollback:
                    agent = on_rollback(rollback_info)
                else:
                    self.rollback_manager.display_rollback_summary(rollback_info)
                    agent = rollback_info["agent"]

        return agent

    def _default_exit_handler(self, agent, current_user):
        """Default handler for conversation exit."""
        print("\n📝 Would you like to name this session?")
        session_name = input("Session name (press Enter to skip): ").strip()

        if session_name:
            self.session_manager.update_session_name(
                agent.session_id,
                session_name
            )
            print(f"✅ Session saved as: {session_name}")

        self.session_manager.update_session_activity(
            agent.session_id,
            current_user.user_id
        )
