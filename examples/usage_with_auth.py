"""Rollback agent with user authentication and session management."""
import sys
from pathlib import Path
from datetime import datetime
import json
import getpass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rollback_agent.agent import create_rollback_agent
from src.rollback_agent.auth.user_manager import UserManager
from src.rollback_agent.utils.database import init_database, get_db_connection
from src.rollback_agent.utils.serialization import serialize_datetimes
from src.rollback_agent.models.checkpoint import Checkpoint

def display_menu(current_user):
    """Display main menu after login."""
    print(f"\n=== Rollback Agent - Welcome {current_user.username} ===")
    print("1. Start New Session")
    print("2. Resume Existing Session")
    print("3. Complete Pending Rollback")
    print("4. Logout")
    return input("\nChoose option (1-4): ")


def display_sessions(sessions):
    """Display available sessions."""
    if not sessions:
        print("\nNo existing sessions found.")
        return None

    print("\n=== Available Sessions ===")
    for i, session in enumerate(sessions, 1):
        name = session['session_name']
        last_activity = session['last_activity'] or 'Never'
        status = "Active" if session['is_active'] else "Inactive"
        print(f"{i}. {name} - Last activity: {last_activity} ({status})")
        if session['parent_session_id']:
            print(f"   (Rolled back from: {session['parent_session_id'][:8]}...)")

    choice = input("\nSelect session number (or 'back' to return): ")
    if choice.lower() == 'back':
        return None

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            return sessions[idx]
    except ValueError:
        pass

    print("Invalid selection.")
    return None


def display_rollbacks(rollbacks):
    """Display pending rollbacks."""
    if not rollbacks:
        print("\nNo pending rollbacks found.")
        return None

    print("\n=== Pending Rollbacks ===")
    for i, rollback in enumerate(rollbacks, 1):
        checkpoint_data = json.loads(rollback['checkpoint_data'])
        checkpoint = Checkpoint.from_dict(checkpoint_data)
        print(f"{i}. Session: {rollback['original_session_id'][:8]}...")
        print(f"   Checkpoint: {checkpoint.name}")
        print(f"   Created: {rollback['rollback_timestamp']}")

    choice = input("\nSelect rollback number (or 'back' to return): ")
    if choice.lower() == 'back':
        return None

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(rollbacks):
            return rollbacks[idx]
    except ValueError:
        pass

    print("Invalid selection.")
    return None


def update_session_activity(session_id: str, user_id: int, db_file: str = "data/rollback_agent.db"):
    """Update last activity timestamp for a session."""
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE rollback_sessions 
            SET last_activity = CURRENT_TIMESTAMP,
                user_id = ?
            WHERE session_id = ?
        """, (user_id, session_id))
        conn.commit()
    finally:
        conn.close()


def run_session(session_id: str, current_user):
    """Run a chat session."""
    agent = create_rollback_agent(
        session_id=session_id,
        user_id=str(current_user.user_id),
        auto_checkpoint_interval=999  # Disable auto checkpoints
    )

    agent.session_state["current_user_id"] = current_user.user_id
    print(f"\n🤖 Session Started: {agent.session_id}")
    print("Commands: 'create checkpoint', 'list checkpoints', 'rollback', 'quit'\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            print("\n📝 Would you like to name this session?")
            session_name = input("Session name (press Enter to skip): ").strip()
            if session_name:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE rollback_sessions 
                    SET session_name = ?
                    WHERE session_id = ?
                """, (session_name, agent.session_id))
                conn.commit()
                conn.close()
                print(f"✅ Session saved as: {session_name}")
            update_session_activity(agent.session_id, current_user.user_id)
            break

        # Get response
        response = agent.run(user_input, user_id=str(current_user.user_id))
        print(f"\nAgent: {response.content}\n")
        
        # If this is the first run after rollback, update parent session info
        if agent.session_state.get("needs_parent_update"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE rollback_sessions 
                SET parent_session_id = ?,
                    session_name = ?
                WHERE session_id = ?
            """, (
                agent.session_state.get("parent_session_id"),
                f"Rollback from {agent.session_state.get('parent_session_id', 'unknown')[:8]}",
                agent.session_id
            ))
            conn.commit()
            conn.close()
            # Remove the flag
            agent.session_state.pop("needs_parent_update", None)

        # Update message counter
        agent.session_state["message_counter"] += 1

        # Update last activity
        update_session_activity(agent.session_id, current_user.user_id)

        # Check if rollback was requested
        if agent.session_state.get("rollback_completed"):
            print("\n🔄 Rollback detected. Completing rollback immediately...")

            # Save rollback information
            new_session_id = agent.session_state.get("new_session_id", "rollback_session")
            conversation_to_restore = agent.session_state.get("rollback_conversation", [])
            old_session_state = agent.session_state.copy()
            old_session_id = agent.session_id
            # Create new agent with new session
            agent = create_rollback_agent(session_id=new_session_id, user_id=str(current_user.user_id))
            
            # Store current user in session state for checkpoint tracking
            agent.session_state["current_user_id"] = current_user.user_id
            agent.session_state["parent_session_id"] = old_session_id
            agent.session_state["needs_parent_update"] = True
            # Restore session state from old agent (including checkpoints)
            for key, value in old_session_state.items():
                if key not in ["rollback_completed", "rollback_conversation", "new_session_id"]:
                    agent.session_state[key] = serialize_datetimes(value)

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

            # Update the session_id for the loop to continue with new session
            session_id = new_session_id
            


def main():
    """Main entry point."""
    # Initialize database
    init_database()

    # User authentication
    user_manager = UserManager()
    current_user = None

    print("=== Rollback Agent - Login ===")

    while not current_user:
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("\nChoose option (1-3): ")

        if choice == "1":
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            current_user = user_manager.login(username, password)

            if current_user:
                print(f"\n✅ Welcome back, {username}!")
            else:
                print("\n❌ Invalid username or password.")

        elif choice == "2":
            username = input("Choose username: ")
            password = getpass.getpass("Choose password: ")
            password_confirm = getpass.getpass("Confirm password: ")

            if password != password_confirm:
                print("\n❌ Passwords do not match.")
                continue

            success, message = user_manager.register(username, password)
            print(f"\n{'✅' if success else '❌'} {message}")

            if success:
                current_user = user_manager.login(username, password)

        elif choice == "3":
            print("\nGoodbye!")
            return

    # Main menu loop
    while True:
        choice = display_menu(current_user)

        if choice == "1":
            # Start new session
            run_session(
                session_id=None,  # Will auto-generate
                current_user=current_user,
            )

        elif choice == "2":
            # Resume existing session
            sessions = user_manager.get_user_sessions(current_user.user_id)
            selected_session = display_sessions(sessions)

            if selected_session:
                run_session(
                    session_id=selected_session['session_id'],
                    current_user=current_user
                )

        elif choice == "3":
            # Complete pending rollback
            rollbacks = user_manager.get_pending_rollbacks(current_user.user_id)
            selected_rollback = display_rollbacks(rollbacks)

            if selected_rollback:
                print("\n🔄 Completing rollback...")
                # TODO: Implement rollback completion logic
                print("✅ Rollback functionality to be implemented")

        elif choice == "4":
            print(f"\nGoodbye, {current_user.username}!")
            break

        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
