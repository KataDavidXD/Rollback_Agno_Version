#!/usr/bin/env python3
"""
Test script to verify rollback functionality preserves conversation history.

This script tests that when we rollback to a checkpoint, the new agent
has access to the conversation history from before the checkpoint.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_config import get_database_path
from src.auth.auth_service import AuthService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.agents.agent_service import AgentService

def test_rollback_with_history():
    """Test that rollback preserves conversation history."""
    
    # Initialize database
    print("Initializing database...")
    db_path = get_database_path()
    print(f"Using database: {db_path}")
    
    # Create auth service and login as rootusr
    auth_service = AuthService()
    success, user, message = auth_service.login("rootusr", "1234")
    if not success or not user:
        print(f"Failed to authenticate as rootusr: {message}")
        return
    
    print(f"Authenticated as: {user.username}")
    
    # Create external session
    external_session_repo = ExternalSessionRepository()
    external_session = ExternalSession(
        user_id=user.id,
        session_name="Test Rollback History"
    )
    external_session = external_session_repo.create(external_session)
    print(f"Created external session: {external_session.id}")
    
    # Create agent service
    agent_service = AgentService(model_config={
        "id": "gpt-4o-mini",
        "temperature": 0.7
    })
    
    # Create new agent
    print("\n=== Creating new agent ===")
    agent = agent_service.create_new_agent(external_session.id)
    
    # Have a conversation
    print("\n=== Initial conversation ===")
    
    # Message 1
    print("User: My name is Alice and I love hiking")
    response1 = agent.run("My name is Alice and I love hiking")
    print(f"Assistant: {response1.content if hasattr(response1, 'content') else response1}")
    
    # Message 2
    print("\nUser: What's my favorite activity?")
    response2 = agent.run("What's my favorite activity?")
    print(f"Assistant: {response2.content if hasattr(response2, 'content') else response2}")
    
    # Create a checkpoint
    print("\n=== Creating checkpoint ===")
    print("User: Create a checkpoint called 'Before Math'")
    response3 = agent.run("Create a checkpoint called 'Before Math'")
    print(f"Assistant: {response3.content if hasattr(response3, 'content') else response3}")
    
    # Continue conversation
    print("\n=== Continuing conversation ===")
    print("User: Let's talk about math instead. What's 2+2?")
    response4 = agent.run("Let's talk about math instead. What's 2+2?")
    print(f"Assistant: {response4.content if hasattr(response4, 'content') else response4}")
    
    print("\nUser: And what's 10*10?")
    response5 = agent.run("And what's 10*10?")
    print(f"Assistant: {response5.content if hasattr(response5, 'content') else response5}")
    
    # List checkpoints
    print("\n=== Listing checkpoints ===")
    checkpoints = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    
    print("Available checkpoints:")
    for cp in checkpoints:
        checkpoint_type = "auto" if cp.is_auto else "manual"
        name = cp.checkpoint_name or "Unnamed"
        print(f"  - ID: {cp.id} | {name} | Type: {checkpoint_type}")
    
    # Find the "Before Math" checkpoint
    before_math_checkpoint = None
    for cp in checkpoints:
        if cp.checkpoint_name and "Before Math" in cp.checkpoint_name:
            before_math_checkpoint = cp
            break
    
    if not before_math_checkpoint:
        print("ERROR: Could not find 'Before Math' checkpoint")
        return
    
    # Rollback to checkpoint
    print(f"\n=== Rolling back to checkpoint {before_math_checkpoint.id} ===")
    new_agent = agent_service.rollback_to_checkpoint(
        external_session.id,
        before_math_checkpoint.id
    )
    
    if not new_agent:
        print("ERROR: Rollback failed")
        return
    
    print("Rollback successful - created new agent")
    
    # Test if the new agent remembers the conversation before checkpoint
    print("\n=== Testing memory after rollback ===")
    
    print("User: Do you remember my name and what I told you I love?")
    response6 = new_agent.run("Do you remember my name and what I told you I love?")
    print(f"Assistant: {response6.content if hasattr(response6, 'content') else response6}")
    
    # Check if agent knows about Alice and hiking
    response_text = str(response6.content if hasattr(response6, 'content') else response6).lower()
    if "alice" in response_text and "hiking" in response_text:
        print("\n✅ SUCCESS: Agent remembers conversation history after rollback!")
    else:
        print("\n❌ FAILURE: Agent doesn't remember conversation history after rollback")
        print("   Expected to mention 'Alice' and 'hiking'")
    
    # Verify math conversation is gone
    print("\nUser: What math problems did we discuss?")
    response7 = new_agent.run("What math problems did we discuss?")
    print(f"Assistant: {response7.content if hasattr(response7, 'content') else response7}")
    
    response_text = str(response7.content if hasattr(response7, 'content') else response7).lower()
    if "2+2" not in response_text and "10*10" not in response_text:
        print("\n✅ SUCCESS: Math conversation correctly not in history after rollback")
    else:
        print("\n❌ WARNING: Math conversation still in history (should have been rolled back)")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_rollback_with_history()