"""Basic usage example of the rollback agent."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rollback_agent.agent import create_rollback_agent


def main():
    """Run basic example."""
    # Create the agent
    agent = create_rollback_agent()
    
    print("🤖 Rollback Agent Started!")
    print("Commands: 'create checkpoint', 'list checkpoints', 'delete checkpoint', 'rollback', 'quit'\n")

    # Interactive loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        # Get response
        response = agent.run(user_input)
        print(f"\nAgent: {response.content}\n")

        # Update message counter
        agent.session_state["message_counter"] += 1
            
        # Check if rollback was requested
        if agent.session_state.get("rollback_completed"):
            print("\n🔄 Rollback detected. Completing rollback...")
            
            # Save rollback information
            new_session_id = agent.session_state.get("new_session_id", "rollback_session")
            conversation_to_restore = agent.session_state.get("rollback_conversation", [])
            old_session_state = agent.session_state.copy()
            
            # Create new agent with new session
            agent = create_rollback_agent(session_id=new_session_id)
            
            # Restore session state from old agent (including checkpoints)
            for key, value in old_session_state.items():
                if key not in ["rollback_completed", "rollback_conversation", "new_session_id"]:
                    agent.session_state[key] = value
            
            # Process and restore conversation context
            if conversation_to_restore:
                context_lines = ["Previous conversation before rollback:"]
                print("\n--- Restored Conversation History ---")
                for msg in conversation_to_restore:
                    role = msg.get('role', 'unknown').capitalize()
                    content = msg.get('content', '')
                    if role != "System":  # Skip system messages for context
                        context_lines.append(f"{role}: {content}")
                    print(f"{role}: {content}")
                print("--- End of Restored History ---\n")
                agent.session_state["restored_conversation_context"] = "\n".join(context_lines)
            else:
                agent.session_state["restored_conversation_context"] = ""
            
            print(f"✅ Rollback completed! Now using session: {new_session_id}")
            print(f"📜 Restored {len(conversation_to_restore)} messages from checkpoint")
            print("You can continue the conversation from the checkpoint.\n")


if __name__ == "__main__":
    main()
