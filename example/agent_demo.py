#!/usr/bin/env python3
"""Example demonstrating the RollbackAgent with checkpoint management.

This shows how to:
1. Create an agent with an external session
2. Have a conversation with automatic checkpointing
3. Use checkpoint tools through natural language
4. Handle rollback operations
"""

import sys
import os
import asyncio
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agno.models.openai import OpenAIChat
from src.agents.agent_service import AgentService
from src.agents.rollback_agent import RollbackAgent
from src.auth.auth_service import AuthService
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.sessions.external_session import ExternalSession
from datetime import datetime


class AgentDemo:
    """Demo class showing RollbackAgent capabilities."""
    
    def __init__(self):
        """Initialize the demo with required services."""
        self.user_repo = UserRepository()
        self.auth_service = AuthService(self.user_repo)
        self.external_session_repo = ExternalSessionRepository()
        self.agent_service = AgentService(
            model_config={
                "id": "gpt-4o-mini",
                "temperature": 0.7
            }
        )
        self.current_agent: Optional[RollbackAgent] = None
        self.current_external_session: Optional[ExternalSession] = None
    
    def setup_demo_user(self) -> int:
        """Create or get a demo user.
        
        Returns:
            User ID of the demo user.
        """
        # Try to login as demo user
        success, user, _ = self.auth_service.login("demo_user", "demo123")
        
        if not success:
            # Register demo user
            success, user, message = self.auth_service.register(
                "demo_user", "demo123", "demo123"
            )
            if success:
                # Login after registration
                success, user, _ = self.auth_service.login("demo_user", "demo123")
        
        if success and user:
            print(f"✓ Demo user ready: {user.username}")
            return user.id
        else:
            raise Exception("Failed to setup demo user")
    
    def create_demo_session(self, user_id: int) -> ExternalSession:
        """Create a demo external session.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            The created external session.
        """
        session = ExternalSession(
            user_id=user_id,
            session_name=f"Demo Session {datetime.now().strftime('%H:%M')}",
            created_at=datetime.now()
        )
        
        saved_session = self.external_session_repo.create(session)
        print(f"✓ Created external session: {saved_session.session_name} (ID: {saved_session.id})")
        return saved_session
    
    def run_conversation(self):
        """Run an interactive conversation with the agent."""
        print("\n" + "="*60)
        print("Starting Agent Conversation")
        print("="*60)
        print("\nYou can:")
        print("• Chat normally with the agent")
        print("• Say 'create checkpoint [name]' to save state")
        print("• Say 'list checkpoints' to see all checkpoints")
        print("• Say 'rollback to checkpoint [id]' to restore")
        print("• Say 'show info about checkpoint [id]' for details")
        print("• Say 'cleanup old checkpoints' to remove old auto-checkpoints")
        print("• Type 'exit' to quit")
        print("\n" + "-"*60 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("\nExiting conversation...")
                    break
                
                if not user_input:
                    continue
                
                # Run the agent
                print("\nAgent: ", end="", flush=True)
                response = self.current_agent.run(user_input)
                
                # Print response
                if hasattr(response, 'content'):
                    print(response.content)
                else:
                    print(response)
                
                # Check for rollback request
                if self.agent_service.handle_agent_response(self.current_agent, response):
                    checkpoint_id = self.current_agent.session_state.get('rollback_checkpoint_id')
                    print(f"\n🔄 Performing rollback to checkpoint {checkpoint_id}...")
                    
                    # Clear the checkpoint_id now that we have it
                    self.current_agent.session_state['rollback_checkpoint_id'] = None
                    
                    # Perform the rollback
                    new_agent = self.agent_service.rollback_to_checkpoint(
                        self.current_external_session.id,
                        checkpoint_id
                    )
                    
                    if new_agent:
                        self.current_agent = new_agent
                        print("✓ Rollback successful! Conversation restored to checkpoint state.")
                        
                        # Show conversation summary
                        summary = self.agent_service.get_conversation_summary(new_agent)
                        print(f"\n{summary}")
                    else:
                        print("✗ Rollback failed.")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
    
    def run_demo(self):
        """Run the complete demo."""
        print("\n🚀 Starting Rollback Agent Demo\n")
        
        try:
            # Setup user and session
            user_id = self.setup_demo_user()
            self.current_external_session = self.create_demo_session(user_id)
            
            # Create agent
            print("\n📤 Creating RollbackAgent...")
            self.current_agent = self.agent_service.create_new_agent(
                external_session_id=self.current_external_session.id,
                session_name="Demo Agent Session"
            )
            print(f"✓ Agent created with session ID: {self.current_agent.agno_session_id}")
            
            # Show checkpoint status
            checkpoints = self.agent_service.list_checkpoints(
                self.current_agent.internal_session.id
            )
            print(f"✓ Current checkpoints: {len(checkpoints)}")
            
            # Run conversation
            self.run_conversation()
            
            # Show final statistics
            print("\n" + "="*60)
            print("Demo Complete - Session Statistics")
            print("="*60)
            
            # Get final checkpoint count
            if self.current_agent and self.current_agent.internal_session:
                final_checkpoints = self.agent_service.list_checkpoints(
                    self.current_agent.internal_session.id
                )
                
                auto_count = sum(1 for cp in final_checkpoints if cp.is_auto)
                manual_count = sum(1 for cp in final_checkpoints if not cp.is_auto)
                
                print(f"Total Checkpoints: {len(final_checkpoints)}")
                print(f"  • Automatic: {auto_count}")
                print(f"  • Manual: {manual_count}")
                
                # Show conversation length
                history = self.current_agent.get_conversation_history()
                print(f"Conversation Length: {len(history)} messages")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point for the demo."""
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nThe demo will continue but agent responses may fail.\n")
    
    demo = AgentDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()