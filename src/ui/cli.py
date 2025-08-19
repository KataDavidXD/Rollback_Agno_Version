"""Command-line interface for the rollback agent system."""

import getpass
from typing import Optional, Tuple
from datetime import datetime

from src.auth.auth_service import AuthService
from src.auth.user import User
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.database.repositories.internal_session_repository import InternalSessionRepository
from src.database.repositories.checkpoint_repository import CheckpointRepository
from src.sessions.external_session import ExternalSession


class CLI:
    """Command-line interface for interacting with the rollback agent system.
    
    Provides user authentication, session management, and agent interaction.
    """
    
    def __init__(self):
        """Initialize the CLI with necessary services and repositories."""
        self.user_repo = UserRepository()
        self.auth_service = AuthService(self.user_repo)
        self.external_session_repo = ExternalSessionRepository()
        self.internal_session_repo = InternalSessionRepository()
        self.checkpoint_repo = CheckpointRepository()
        self.current_user: Optional[User] = None
        self.current_external_session: Optional[ExternalSession] = None
    
    def run(self):
        """Main entry point for the CLI."""
        self._print_welcome()
        
        while not self.current_user:
            self._auth_menu()
        
        self._main_menu()
    
    def _print_welcome(self):
        """Print welcome message."""
        print("\n" + "="*60)
        print("Welcome to the Rollback Agent System")
        print("="*60)
    
    def _auth_menu(self):
        """Display authentication menu and handle user choice."""
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            self._login()
        elif choice == "2":
            self._register()
        elif choice == "3":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")
    
    def _login(self):
        """Handle user login."""
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        success, user, message = self.auth_service.login(username, password)
        print(f"\n{message}")
        
        if success:
            self.current_user = user
    
    def _register(self):
        """Handle user registration."""
        print("\n--- Register ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")
        
        success, user, message = self.auth_service.register(
            username, password, confirm_password
        )
        print(f"\n{message}")
        
        if success:
            print("Please login with your new credentials.")
    
    def _main_menu(self):
        """Display main menu based on user role."""
        while True:
            print(f"\n--- Main Menu (Logged in as: {self.current_user.username}) ---")
            print("1. Start New Session")
            print("2. Resume Existing Session")
            print("3. List My Sessions")
            
            if self.current_user.is_admin:
                print("4. User Management (Admin)")
            
            print("0. Logout")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == "1":
                self._start_new_session()
            elif choice == "2":
                self._resume_session()
            elif choice == "3":
                self._list_sessions()
            elif choice == "4" and self.current_user.is_admin:
                self._user_management()
            elif choice == "0":
                self._logout()
                break
            else:
                print("Invalid choice. Please try again.")
    
    def _start_new_session(self):
        """Start a new external session."""
        print("\n--- Start New Session ---")
        session_name = input("Enter session name (or press Enter for default): ").strip()
        
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create new external session
        external_session = ExternalSession(
            user_id=self.current_user.id,
            session_name=session_name,
            created_at=datetime.now()
        )
        
        saved_session = self.external_session_repo.create(external_session)
        self.current_external_session = saved_session
        
        print(f"\n✓ Created new session: {session_name} (ID: {saved_session.id})")
        
        # Launch agent interaction
        self._agent_interaction()
    
    def _resume_session(self):
        """Resume an existing session."""
        sessions = self.external_session_repo.get_user_sessions(
            self.current_user.id, active_only=True
        )
        
        if not sessions:
            print("\nNo active sessions found.")
            return
        
        print("\n--- Your Active Sessions ---")
        for i, session in enumerate(sessions, 1):
            created = session.created_at.strftime('%Y-%m-%d %H:%M') if session.created_at else "unknown"
            internal_count = len(session.internal_session_ids)
            print(f"{i}. {session.session_name} (ID: {session.id}) - Created: {created} - {internal_count} internal sessions")
        
        try:
            choice = int(input("\nSelect session number (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(sessions):
                self.current_external_session = sessions[choice - 1]
                print(f"\n✓ Resumed session: {self.current_external_session.session_name}")
                self._agent_interaction()
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
    
    def _list_sessions(self):
        """List all user sessions."""
        sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
        
        if not sessions:
            print("\nNo sessions found.")
            return
        
        print("\n--- Your Sessions ---")
        for session in sessions:
            status = "Active" if session.is_active else "Inactive"
            created = session.created_at.strftime('%Y-%m-%d %H:%M') if session.created_at else "unknown"
            internal_count = len(session.internal_session_ids)
            print(f"• {session.session_name} (ID: {session.id})")
            print(f"  Status: {status} | Created: {created} | Internal Sessions: {internal_count}")
    
    def _user_management(self):
        """Admin user management menu."""
        while True:
            print("\n--- User Management (Admin) ---")
            print("1. List All Users")
            print("2. Delete User")
            print("3. Reset Admin Password")
            print("0. Back to Main Menu")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == "1":
                self._list_users()
            elif choice == "2":
                self._delete_user()
            elif choice == "3":
                self._reset_admin_password()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
    
    def _list_users(self):
        """List all users (admin only)."""
        users = self.user_repo.find_all()
        
        print("\n--- All Users ---")
        for user in users:
            role = "Admin" if user.is_admin else "User"
            created = user.created_at.strftime('%Y-%m-%d') if user.created_at else "unknown"
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else "never"
            print(f"• {user.username} (ID: {user.id})")
            print(f"  Role: {role} | Created: {created} | Last Login: {last_login}")
    
    def _delete_user(self):
        """Delete a user (admin only)."""
        username = input("\nEnter username to delete: ").strip()
        
        if username == self.current_user.username:
            print("You cannot delete your own account.")
            return
        
        confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            success, message = self.auth_service.delete_user(
                self.current_user.id, username
            )
            print(f"\n{message}")
        else:
            print("Deletion cancelled.")
    
    def _reset_admin_password(self):
        """Reset the admin password."""
        print("\n--- Reset Admin Password ---")
        current_password = getpass.getpass("Current admin password: ")
        new_password = getpass.getpass("New password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            print("Passwords do not match.")
            return
        
        success, message = self.auth_service.reset_admin_password(
            current_password, new_password
        )
        print(f"\n{message}")
    
    def _agent_interaction(self):
        """Handle interaction with the agent.
        
        This is a placeholder for the actual agent interaction.
        In a real implementation, this would create/resume a RollbackAgent.
        """
        print("\n--- Agent Interaction ---")
        print(f"Session: {self.current_external_session.session_name}")
        print("\nAgent interaction would start here.")
        print("Features available:")
        print("• Natural language conversation")
        print("• Automatic checkpointing after tool calls")
        print("• Manual checkpoint creation via 'create checkpoint'")
        print("• List checkpoints via 'list checkpoints'")
        print("• Rollback via 'rollback to checkpoint [ID]'")
        print("\n(Returning to main menu for this demo)")
    
    def _logout(self):
        """Log out the current user."""
        print(f"\nLogging out {self.current_user.username}...")
        self.current_user = None
        self.current_external_session = None
        print("✓ Logged out successfully.")


def main():
    """Main entry point for the CLI application."""
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nExiting... Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please try again or contact support.")


if __name__ == "__main__":
    main()