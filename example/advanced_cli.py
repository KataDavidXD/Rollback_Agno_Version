#!/usr/bin/env python3
"""
Advanced CLI System for Rollback Agent
Provides comprehensive user, session, and agent management.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import getpass
from enum import Enum

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.auth_service import AuthService
from src.auth.user import User
from src.sessions.external_session import ExternalSession
from src.sessions.internal_session import InternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.database.repositories.internal_session_repository import InternalSessionRepository
from src.database.repositories.user_repository import UserRepository
from src.agents.agent_service import AgentService
from src.agents.rollback_agent import RollbackAgent


class MenuChoice(Enum):
    """Menu choices for navigation."""
    BACK = "0"
    EXIT = "99"


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.WARNING = ''
        cls.FAIL = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''


class AdvancedCLI:
    """Advanced CLI for comprehensive system management."""
    
    def __init__(self):
        """Initialize the CLI system."""
        self.auth_service = AuthService()
        self.external_session_repo = ExternalSessionRepository()
        self.internal_session_repo = InternalSessionRepository()
        self.user_repo = UserRepository()
        self.agent_service = None  # Initialized after login
        self.current_user: Optional[User] = None
        self.current_external_session: Optional[ExternalSession] = None
        self.current_agent: Optional[RollbackAgent] = None
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")
    
    def get_choice(self, prompt: str) -> str:
        """Get user choice with colored prompt."""
        return input(f"{Colors.BLUE}▶ {prompt}: {Colors.ENDC}").strip()
    
    def pause(self):
        """Pause for user input."""
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
    
    # ========== Authentication ==========
    
    def auth_menu(self) -> bool:
        """Show authentication menu.
        
        Returns:
            True if authenticated, False to exit.
        """
        while True:
            self.clear_screen()
            self.print_header("ROLLBACK AGENT SYSTEM")
            
            print("1. Login")
            print("2. Register")
            print("0. Exit")
            print()
            
            choice = self.get_choice("Enter choice")
            
            if choice == "1":
                if self.login():
                    return True
            elif choice == "2":
                if self.register():
                    return True
            elif choice == "0":
                return False
            else:
                self.print_error("Invalid choice")
                self.pause()
    
    def login(self) -> bool:
        """Handle user login.
        
        Returns:
            True if successful, False otherwise.
        """
        self.clear_screen()
        self.print_header("LOGIN")
        
        username = self.get_choice("Username")
        password = getpass.getpass(f"{Colors.BLUE}▶ Password: {Colors.ENDC}")
        
        success, user, message = self.auth_service.login(username, password)
        
        if success and user:
            self.current_user = user
            self.agent_service = AgentService()
            self.print_success(f"Welcome back, {user.username}!")
            self.pause()
            return True
        else:
            self.print_error(f"Login failed: {message}")
            self.pause()
            return False
    
    def register(self) -> bool:
        """Handle user registration.
        
        Returns:
            True if successful, False otherwise.
        """
        self.clear_screen()
        self.print_header("REGISTER")
        
        username = self.get_choice("Choose username")
        password = getpass.getpass(f"{Colors.BLUE}▶ Choose password: {Colors.ENDC}")
        confirm = getpass.getpass(f"{Colors.BLUE}▶ Confirm password: {Colors.ENDC}")
        
        if password != confirm:
            self.print_error("Passwords don't match")
            self.pause()
            return False
        
        success, user, message = self.auth_service.register(username, password)
        
        if success and user:
            self.current_user = user
            self.agent_service = AgentService()
            self.print_success(f"Registration successful! Welcome, {user.username}!")
            self.pause()
            return True
        else:
            self.print_error(f"Registration failed: {message}")
            self.pause()
            return False
    
    # ========== Main Menu ==========
    
    def main_menu(self):
        """Show main menu after authentication."""
        while True:
            self.clear_screen()
            self.print_header("MAIN MENU")
            print(f"Logged in as: {Colors.BOLD}{self.current_user.username}{Colors.ENDC}")
            if self.current_user.is_admin:
                print(f"Role: {Colors.WARNING}Administrator{Colors.ENDC}")
            print()
            
            print("1. Session Management")
            print("2. User Profile")
            if self.current_user.is_admin:
                print("3. Admin Panel")
            print("0. Logout")
            print()
            
            choice = self.get_choice("Enter choice")
            
            if choice == "1":
                self.session_management_menu()
            elif choice == "2":
                self.user_profile_menu()
            elif choice == "3" and self.current_user.is_admin:
                self.admin_menu()
            elif choice == "0":
                self.print_info("Logging out...")
                break
            else:
                self.print_error("Invalid choice")
                self.pause()
    
    # ========== Session Management ==========
    
    def session_management_menu(self):
        """Show session management menu."""
        while True:
            self.clear_screen()
            self.print_header("SESSION MANAGEMENT")
            
            # Get user's external sessions
            external_sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
            
            print(f"You have {Colors.BOLD}{len(external_sessions)}{Colors.ENDC} session(s)\n")
            
            print("1. Create New Session")
            print("2. List My Sessions")
            print("3. Resume Session")
            print("4. Delete Session")
            print("0. Back to Main Menu")
            print()
            
            choice = self.get_choice("Enter choice")
            
            if choice == "1":
                self.create_new_session()
            elif choice == "2":
                self.list_sessions()
            elif choice == "3":
                self.resume_session()
            elif choice == "4":
                self.delete_session()
            elif choice == "0":
                break
            else:
                self.print_error("Invalid choice")
                self.pause()
    
    def create_new_session(self):
        """Create a new external session."""
        self.clear_screen()
        self.print_header("CREATE NEW SESSION")
        
        session_name = self.get_choice("Session name (or press Enter for default)")
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        external_session = ExternalSession(
            user_id=self.current_user.id,
            session_name=session_name
        )
        
        external_session = self.external_session_repo.create(external_session)
        
        if external_session:
            self.print_success(f"Created session: {session_name}")
            
            # Ask if user wants to start chatting immediately
            if self.get_choice("Start chatting now? (y/n)").lower() == 'y':
                self.current_external_session = external_session
                self.start_new_internal_session()
        else:
            self.print_error("Failed to create session")
        
        self.pause()
    
    def list_sessions(self):
        """List all user's external sessions with hierarchy."""
        self.clear_screen()
        self.print_header("MY SESSIONS")
        
        external_sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
        
        if not external_sessions:
            self.print_info("No sessions found")
        else:
            for ext_session in external_sessions:
                # Display external session
                created = ext_session.created_at.strftime('%Y-%m-%d %H:%M') if ext_session.created_at else "Unknown"
                print(f"\n{Colors.BOLD}📁 {ext_session.session_name}{Colors.ENDC}")
                print(f"   ID: {ext_session.id} | Created: {created}")
                
                # Get internal sessions for this external session
                internal_sessions = self.internal_session_repo.get_by_external_session(ext_session.id)
                
                if internal_sessions:
                    print(f"   {Colors.CYAN}Internal Sessions:{Colors.ENDC}")
                    for int_session in internal_sessions:
                        status = "✓ Current" if int_session.is_current else "  "
                        created = int_session.created_at.strftime('%m-%d %H:%M') if int_session.created_at else "Unknown"
                        checkpoint_count = int_session.checkpoint_count or 0
                        
                        print(f"     {status} ID: {int_session.id} | "
                              f"Created: {created} | "
                              f"Checkpoints: {checkpoint_count}")
                else:
                    print(f"   {Colors.WARNING}No internal sessions{Colors.ENDC}")
        
        self.pause()
    
    def resume_session(self):
        """Resume an existing session."""
        self.clear_screen()
        self.print_header("RESUME SESSION")
        
        external_sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
        
        if not external_sessions:
            self.print_info("No sessions to resume")
            self.pause()
            return
        
        # Display sessions to choose from
        print("Available sessions:\n")
        for i, ext_session in enumerate(external_sessions, 1):
            created = ext_session.created_at.strftime('%Y-%m-%d %H:%M') if ext_session.created_at else "Unknown"
            print(f"{i}. {ext_session.session_name} (Created: {created})")
        
        print("\n0. Cancel")
        
        # Get external session choice
        choice = self.get_choice("Select session")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(external_sessions):
                self.current_external_session = external_sessions[idx]
                self.select_internal_session()
            else:
                self.print_error("Invalid selection")
                self.pause()
        except ValueError:
            self.print_error("Invalid input")
            self.pause()
    
    def select_internal_session(self):
        """Select which internal session to resume or create new."""
        self.clear_screen()
        self.print_header(f"SESSION: {self.current_external_session.session_name}")
        
        internal_sessions = self.internal_session_repo.get_by_external_session(
            self.current_external_session.id
        )
        
        if not internal_sessions:
            self.print_info("No internal sessions found. Creating new one...")
            self.start_new_internal_session()
            return
        
        print("Internal sessions:\n")
        for i, int_session in enumerate(internal_sessions, 1):
            status = "✓" if int_session.is_current else " "
            created = int_session.created_at.strftime('%Y-%m-%d %H:%M') if int_session.created_at else "Unknown"
            print(f"{i}. [{status}] Session {int_session.id} (Created: {created}, "
                  f"Checkpoints: {int_session.checkpoint_count})")
        
        print(f"\n{len(internal_sessions) + 1}. Create new internal session")
        print("0. Cancel")
        
        choice = self.get_choice("Select internal session")
        
        if choice == "0":
            return
        elif choice == str(len(internal_sessions) + 1):
            self.start_new_internal_session()
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(internal_sessions):
                    selected_session = internal_sessions[idx]
                    self.resume_internal_session(selected_session)
                else:
                    self.print_error("Invalid selection")
                    self.pause()
            except ValueError:
                self.print_error("Invalid input")
                self.pause()
    
    def start_new_internal_session(self):
        """Start a new internal session within current external session."""
        self.print_info("Creating new agent session...")
        
        # Create new agent
        self.current_agent = self.agent_service.create_new_agent(
            external_session_id=self.current_external_session.id
        )
        
        if self.current_agent:
            self.print_success("Agent created successfully!")
            self.chat_interface()
        else:
            self.print_error("Failed to create agent")
            self.pause()
    
    def resume_internal_session(self, internal_session: InternalSession):
        """Resume an existing internal session."""
        self.print_info(f"Resuming session {internal_session.id}...")
        
        # Resume the agent
        self.current_agent = self.agent_service.resume_agent(
            external_session_id=self.current_external_session.id,
            internal_session_id=internal_session.id
        )
        
        if self.current_agent:
            self.print_success("Session resumed successfully!")
            
            # Show recent conversation history
            history = self.current_agent.get_conversation_history()
            if history:
                print(f"\n{Colors.CYAN}Recent conversation:{Colors.ENDC}")
                for msg in history[-4:]:  # Show last 2 exchanges
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if len(content) > 100:
                        content = content[:97] + "..."
                    
                    role_color = Colors.GREEN if role == 'assistant' else Colors.BLUE
                    print(f"{role_color}[{role.upper()}]{Colors.ENDC} {content}")
            
            self.chat_interface()
        else:
            self.print_error("Failed to resume session")
            self.pause()
    
    def delete_session(self):
        """Delete an external session and all its data."""
        self.clear_screen()
        self.print_header("DELETE SESSION")
        
        external_sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
        
        if not external_sessions:
            self.print_info("No sessions to delete")
            self.pause()
            return
        
        # Display sessions
        print("Sessions:\n")
        for i, ext_session in enumerate(external_sessions, 1):
            print(f"{i}. {ext_session.session_name}")
        
        print("\n0. Cancel")
        
        choice = self.get_choice("Select session to delete")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(external_sessions):
                session_to_delete = external_sessions[idx]
                
                # Confirm deletion
                confirm = self.get_choice(
                    f"Delete '{session_to_delete.session_name}'? "
                    f"This will delete all internal sessions and checkpoints! (y/n)"
                )
                
                if confirm.lower() == 'y':
                    success = self.external_session_repo.delete(session_to_delete.id)
                    if success:
                        self.print_success("Session deleted successfully")
                    else:
                        self.print_error("Failed to delete session")
                else:
                    self.print_info("Deletion cancelled")
            else:
                self.print_error("Invalid selection")
        except ValueError:
            self.print_error("Invalid input")
        
        self.pause()
    
    # ========== Chat Interface ==========
    
    def chat_interface(self):
        """Interactive chat interface with the agent."""
        self.clear_screen()
        self.print_header(f"CHAT: {self.current_external_session.session_name}")
        
        print(f"{Colors.CYAN}Commands:{Colors.ENDC}")
        print("  /checkpoints - List checkpoints")
        print("  /checkpoint <name> - Create checkpoint")
        print("  /rollback <id/name> - Rollback to checkpoint")
        print("  /history - Show conversation history")
        print("  /clear - Clear screen")
        print("  /exit - Exit chat")
        print()
        print(f"{Colors.WARNING}Type your message or command:{Colors.ENDC}\n")
        
        while True:
            try:
                # Get user input
                user_input = input(f"{Colors.BLUE}You: {Colors.ENDC}")
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not self.handle_chat_command(user_input):
                        break
                    continue
                
                # Send to agent
                print(f"{Colors.GREEN}Agent: {Colors.ENDC}", end="", flush=True)
                response = self.current_agent.run(user_input)
                
                # Display response
                if hasattr(response, 'content'):
                    print(response.content)
                else:
                    print(response)
                
                # Check for rollback request
                if self.agent_service.handle_agent_response(self.current_agent, response):
                    checkpoint_id = self.current_agent.session_state.get('rollback_checkpoint_id')
                    if checkpoint_id:
                        print(f"\n{Colors.WARNING}Performing rollback...{Colors.ENDC}")
                        new_agent = self.agent_service.rollback_to_checkpoint(
                            self.current_external_session.id,
                            checkpoint_id
                        )
                        if new_agent:
                            self.current_agent = new_agent
                            self.print_success("Rollback completed!")
                        else:
                            self.print_error("Rollback failed")
                
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n")
                if self.get_choice("Exit chat? (y/n)").lower() == 'y':
                    break
            except Exception as e:
                self.print_error(f"Error: {e}")
    
    def handle_chat_command(self, command: str) -> bool:
        """Handle chat commands.
        
        Args:
            command: The command string.
            
        Returns:
            True to continue chatting, False to exit.
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/exit":
            return False
        elif cmd == "/clear":
            self.clear_screen()
            self.print_header(f"CHAT: {self.current_external_session.session_name}")
        elif cmd == "/checkpoints":
            self.show_checkpoints()
        elif cmd == "/checkpoint":
            if arg:
                self.create_checkpoint(arg)
            else:
                self.print_error("Usage: /checkpoint <name>")
        elif cmd == "/rollback":
            if arg:
                self.rollback_to_checkpoint(arg)
            else:
                self.print_error("Usage: /rollback <id/name>")
        elif cmd == "/history":
            self.show_history()
        else:
            self.print_error(f"Unknown command: {cmd}")
        
        return True
    
    def show_checkpoints(self):
        """Show available checkpoints."""
        checkpoints = self.current_agent.checkpoint_repo.get_by_internal_session(
            self.current_agent.internal_session.id,
            auto_only=False
        )
        
        if not checkpoints:
            self.print_info("No checkpoints found")
        else:
            print(f"\n{Colors.CYAN}Checkpoints:{Colors.ENDC}")
            for cp in checkpoints:
                cp_type = "AUTO" if cp.is_auto else "MANUAL"
                created = cp.created_at.strftime('%H:%M:%S') if cp.created_at else "Unknown"
                name = cp.checkpoint_name or "Unnamed"
                print(f"  [{cp_type}] ID: {cp.id} | {name} | Created: {created}")
        print()
    
    def create_checkpoint(self, name: str):
        """Create a manual checkpoint."""
        result = self.current_agent.create_checkpoint(name)
        self.print_success(result)
    
    def rollback_to_checkpoint(self, target: str):
        """Rollback to a checkpoint."""
        # First, try to find the checkpoint by ID or name
        checkpoints = self.current_agent.checkpoint_repo.get_by_internal_session(
            self.current_agent.internal_session.id,
            auto_only=False
        )
        
        checkpoint = None
        # Try to parse as ID first
        try:
            checkpoint_id = int(target)
            for cp in checkpoints:
                if cp.id == checkpoint_id:
                    checkpoint = cp
                    break
        except ValueError:
            # Not an ID, try to find by name
            target_lower = target.lower()
            for cp in checkpoints:
                if cp.checkpoint_name and target_lower in cp.checkpoint_name.lower():
                    checkpoint = cp
                    break
        
        if not checkpoint:
            self.print_error(f"Checkpoint '{target}' not found")
            return
        
        # Perform the rollback directly
        print(f"\n{Colors.WARNING}Rolling back to checkpoint {checkpoint.id} ({checkpoint.checkpoint_name})...{Colors.ENDC}")
        
        new_agent = self.agent_service.rollback_to_checkpoint(
            self.current_external_session.id,
            checkpoint.id
        )
        
        if new_agent:
            self.current_agent = new_agent
            self.print_success("Rollback completed successfully!")
            # Show the restored conversation context
            history = new_agent.get_conversation_history()
            if history and len(history) > 0:
                print(f"\n{Colors.CYAN}Restored to this point in conversation:{Colors.ENDC}")
                # Show last exchange
                for msg in history[-2:]:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if len(content) > 100:
                        content = content[:97] + "..."
                    role_color = Colors.GREEN if role == 'assistant' else Colors.BLUE
                    print(f"{role_color}[{role.upper()}]{Colors.ENDC} {content}")
        else:
            self.print_error("Rollback failed")
    
    def show_history(self):
        """Show conversation history."""
        history = self.current_agent.get_conversation_history()
        
        if not history:
            self.print_info("No conversation history")
        else:
            print(f"\n{Colors.CYAN}Conversation History:{Colors.ENDC}")
            for msg in history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                
                role_color = Colors.GREEN if role == 'assistant' else Colors.BLUE
                print(f"\n{role_color}[{role.upper()}]{Colors.ENDC}")
                print(content)
        print()
    
    # ========== User Profile ==========
    
    def user_profile_menu(self):
        """Show user profile menu."""
        self.clear_screen()
        self.print_header("USER PROFILE")
        
        print(f"Username: {Colors.BOLD}{self.current_user.username}{Colors.ENDC}")
        print(f"User ID: {self.current_user.id}")
        print(f"Admin: {'Yes' if self.current_user.is_admin else 'No'}")
        if self.current_user.created_at:
            print(f"Member since: {self.current_user.created_at.strftime('%Y-%m-%d')}")
        
        # Count sessions
        sessions = self.external_session_repo.get_user_sessions(self.current_user.id)
        print(f"Total sessions: {len(sessions)}")
        
        print("\n1. Change Password")
        print("0. Back")
        
        choice = self.get_choice("Enter choice")
        
        if choice == "1":
            self.change_password()
        
        self.pause()
    
    def change_password(self):
        """Change user password."""
        print("\n" + "="*40)
        current = getpass.getpass("Current password: ")
        
        # Verify current password
        success, _, _ = self.auth_service.login(self.current_user.username, current)
        if not success:
            self.print_error("Current password is incorrect")
            return
        
        new_password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm:
            self.print_error("Passwords don't match")
            return
        
        success, message = self.auth_service.change_password(
            self.current_user.username,
            current,
            new_password
        )
        
        if success:
            self.print_success("Password changed successfully")
        else:
            self.print_error(f"Failed to change password: {message}")
    
    # ========== Admin Panel ==========
    
    def admin_menu(self):
        """Show admin panel."""
        if not self.current_user.is_admin:
            self.print_error("Access denied")
            return
        
        while True:
            self.clear_screen()
            self.print_header("ADMIN PANEL")
            
            print("1. List All Users")
            print("2. Delete User")
            print("3. System Statistics")
            print("0. Back")
            print()
            
            choice = self.get_choice("Enter choice")
            
            if choice == "1":
                self.list_all_users()
            elif choice == "2":
                self.delete_user()
            elif choice == "3":
                self.show_statistics()
            elif choice == "0":
                break
            else:
                self.print_error("Invalid choice")
                self.pause()
    
    def list_all_users(self):
        """List all users in the system."""
        self.clear_screen()
        self.print_header("ALL USERS")
        
        users = self.user_repo.find_all()
        
        print(f"Total users: {len(users)}\n")
        
        for user in users:
            admin_badge = " [ADMIN]" if user.is_admin else ""
            created = user.created_at.strftime('%Y-%m-%d') if user.created_at else "Unknown"
            sessions = self.external_session_repo.get_user_sessions(user.id)
            
            print(f"• {user.username}{admin_badge}")
            print(f"  ID: {user.id} | Created: {created} | Sessions: {len(sessions)}")
        
        self.pause()
    
    def delete_user(self):
        """Delete a user (admin only)."""
        self.clear_screen()
        self.print_header("DELETE USER")
        
        username = self.get_choice("Username to delete (0 to cancel)")
        
        if username == "0":
            return
        
        if username == "rootusr":
            self.print_error("Cannot delete rootusr")
            self.pause()
            return
        
        if username == self.current_user.username:
            self.print_error("Cannot delete yourself")
            self.pause()
            return
        
        # Confirm
        confirm = self.get_choice(
            f"Delete user '{username}' and all their data? (y/n)"
        )
        
        if confirm.lower() == 'y':
            success, message = self.auth_service.delete_user(
                username,
                self.current_user.username
            )
            
            if success:
                self.print_success(f"User '{username}' deleted")
            else:
                self.print_error(f"Failed: {message}")
        else:
            self.print_info("Deletion cancelled")
        
        self.pause()
    
    def show_statistics(self):
        """Show system statistics."""
        self.clear_screen()
        self.print_header("SYSTEM STATISTICS")
        
        # Get all users
        users = self.user_repo.find_all()
        admin_count = sum(1 for u in users if u.is_admin)
        
        # Get all sessions
        all_external_sessions = []
        all_internal_sessions = []
        total_checkpoints = 0
        
        for user in users:
            ext_sessions = self.external_session_repo.get_user_sessions(user.id)
            all_external_sessions.extend(ext_sessions)
            
            for ext_session in ext_sessions:
                int_sessions = self.internal_session_repo.get_by_external_session(ext_session.id)
                all_internal_sessions.extend(int_sessions)
                
                for int_session in int_sessions:
                    total_checkpoints += int_session.checkpoint_count or 0
        
        print(f"{Colors.BOLD}Users:{Colors.ENDC}")
        print(f"  Total: {len(users)}")
        print(f"  Admins: {admin_count}")
        print(f"  Regular: {len(users) - admin_count}")
        
        print(f"\n{Colors.BOLD}Sessions:{Colors.ENDC}")
        print(f"  External Sessions: {len(all_external_sessions)}")
        print(f"  Internal Sessions: {len(all_internal_sessions)}")
        print(f"  Total Checkpoints: {total_checkpoints}")
        
        if all_external_sessions:
            avg_internal = len(all_internal_sessions) / len(all_external_sessions)
            print(f"  Avg Internal/External: {avg_internal:.1f}")
        
        if all_internal_sessions:
            avg_checkpoints = total_checkpoints / len(all_internal_sessions)
            print(f"  Avg Checkpoints/Session: {avg_checkpoints:.1f}")
        
        self.pause()
    
    # ========== Main Run ==========
    
    def run(self):
        """Run the CLI application."""
        # Check if terminal supports colors
        if not sys.stdout.isatty():
            Colors.disable()
        
        try:
            # Authentication
            if not self.auth_menu():
                print("\nGoodbye!")
                return
            
            # Main application
            self.main_menu()
            
            print("\nThank you for using Rollback Agent System!")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
        except Exception as e:
            print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}")
            raise


def main():
    """Entry point for the advanced CLI."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it before running:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    cli = AdvancedCLI()
    cli.run()


if __name__ == "__main__":
    main()