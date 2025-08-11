"""CLI display helpers for rollback agent."""
from typing import List, Dict, Optional, Any
import json
from ..models.checkpoint import Checkpoint


class CLIHelper:
    """Helper functions for CLI display."""

    @staticmethod
    def display_menu(current_user) -> str:
        """Display main menu after login."""
        print(f"\n=== Rollback Agent - Welcome {current_user.username} ===")
        print("1. Start New Session")
        print("2. Resume Existing Session")
        print("3. Complete Pending Rollback")
        print("4. Logout")
        return input("\nChoose option (1-4): ")

    @staticmethod
    def display_sessions(sessions: List[Dict]) -> Optional[Dict]:
        """Display available sessions and get selection."""
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

    @staticmethod
    def display_rollbacks(rollbacks: List[Dict]) -> Optional[Dict]:
        """Display pending rollbacks and get selection."""
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

    @staticmethod
    def display_auth_menu() -> str:
        """Display authentication menu."""
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        return input("\nChoose option (1-3): ")
