"""Main application class for rollback agent framework."""
import getpass
from typing import Optional
from .auth.user_manager import UserManager
from .managers.session_manager import SessionManager
from .managers.conversation_manager import ConversationManager
from .ui.cli_helper import CLIHelper
from .utils.database import init_database


class RollbackAgentApp:
    """Main application for rollback agent."""

    def __init__(self, db_file: str = "data/rollback_agent.db"):
        self.db_file = db_file
        self.user_manager = UserManager(db_file)
        self.session_manager = SessionManager(db_file)
        self.conversation_manager = ConversationManager(self.session_manager)
        self.cli = CLIHelper()
        self.current_user = None

        # Initialize database
        init_database(db_file)

    def authenticate(self) -> bool:
        """Handle user authentication."""
        print("=== Rollback Agent - Login ===")

        while not self.current_user:
            choice = self.cli.display_auth_menu()

            if choice == "1":  # Login
                username = input("Username: ")
                password = getpass.getpass("Password: ")
                self.current_user = self.user_manager.login(username, password)

                if self.current_user:
                    print(f"\n✅ Welcome back, {username}!")
                    return True
                else:
                    print("\n❌ Invalid username or password.")

            elif choice == "2":  # Register
                username = input("Choose username: ")
                password = getpass.getpass("Choose password: ")
                password_confirm = getpass.getpass("Confirm password: ")

                if password != password_confirm:
                    print("\n❌ Passwords do not match.")
                    continue

                success, message = self.user_manager.register(username, password)
                print(f"\n{'✅' if success else '❌'} {message}")

                if success:
                    self.current_user = self.user_manager.login(username, password)
                    return True

            elif choice == "3":  # Exit
                print("\nGoodbye!")
                return False

        return False

    def run(self):
        """Run the main application loop."""
        if not self.authenticate():
            return

        while True:
            choice = self.cli.display_menu(self.current_user)

            if choice == "1":  # New session
                self.start_new_session()

            elif choice == "2":  # Resume session
                self.resume_session()

            elif choice == "3":  # Complete rollback
                self.complete_rollback()

            elif choice == "4":  # Logout
                print(f"\nGoodbye, {self.current_user.username}!")
                break

            else:
                print("\nInvalid choice. Please try again.")

    def start_new_session(self):
        """Start a new conversation session."""
        agent = self.session_manager.create_session(
            user_id=str(self.current_user.user_id),
            auto_checkpoint_interval=999  # Disable auto checkpoints
        )

        self.conversation_manager.run_conversation(
            agent,
            self.current_user
        )

    def resume_session(self):
        """Resume an existing session."""
        sessions = self.user_manager.get_user_sessions(self.current_user.user_id)
        selected_session = self.cli.display_sessions(sessions)

        if selected_session:
            agent = self.session_manager.create_session(
                session_id=selected_session['session_id'],
                user_id=str(self.current_user.user_id)
            )

            self.conversation_manager.run_conversation(
                agent,
                self.current_user
            )

    def complete_rollback(self):
        """Complete a pending rollback."""
        rollbacks = self.user_manager.get_pending_rollbacks(self.current_user.user_id)
        selected_rollback = self.cli.display_rollbacks(rollbacks)

        if selected_rollback:
            print("\n🔄 Completing rollback...")
            # TODO: Implement rollback completion logic
            print("✅ Rollback functionality to be implemented")
