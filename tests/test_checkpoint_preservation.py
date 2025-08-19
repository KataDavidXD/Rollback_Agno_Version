#!/usr/bin/env python3
"""
Test script to verify checkpoint preservation after rollback.

This test checks if the system properly maintains checkpoints after rollback,
allowing full snapshot rollback where you can rollback to ANY previous checkpoint,
not just ones created after the rollback.
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

def test_checkpoint_preservation():
    """Test that checkpoints are preserved after rollback."""
    
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
        session_name="Test Checkpoint Preservation"
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
    
    # Create checkpoint A
    print("\n=== Creating Checkpoint A ===")
    print("User: Create checkpoint A")
    response = agent.run("Create checkpoint A")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Add some conversation
    print("\nUser: Let's talk about dogs")
    response = agent.run("Let's talk about dogs")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Create checkpoint B
    print("\n=== Creating Checkpoint B ===")
    print("User: Create checkpoint B")
    response = agent.run("Create checkpoint B")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Add more conversation
    print("\nUser: Now let's discuss cats")
    response = agent.run("Now let's discuss cats")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Create checkpoint C
    print("\n=== Creating Checkpoint C ===")
    print("User: Create checkpoint C")
    response = agent.run("Create checkpoint C")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # List all checkpoints before rollback
    print("\n=== Listing checkpoints BEFORE rollback ===")
    checkpoints_before = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    
    print("Available checkpoints before rollback:")
    checkpoint_names_before = []
    checkpoint_b_id = None
    for cp in checkpoints_before:
        if not cp.is_auto:  # Only show manual checkpoints
            checkpoint_type = "manual"
            name = cp.checkpoint_name or "Unnamed"
            print(f"  - ID: {cp.id} | {name} | Type: {checkpoint_type}")
            checkpoint_names_before.append(name)
            if "B" in name or "b" in name:
                checkpoint_b_id = cp.id
    
    if not checkpoint_b_id:
        print("ERROR: Could not find checkpoint B")
        return
    
    # Rollback to checkpoint B
    print(f"\n=== Rolling back to checkpoint B (ID: {checkpoint_b_id}) ===")
    new_agent = agent_service.rollback_to_checkpoint(
        external_session.id,
        checkpoint_b_id
    )
    
    if not new_agent:
        print("ERROR: Rollback failed")
        return
    
    print("Rollback successful - created new agent")
    print(f"Old internal session ID: {agent.internal_session.id}")
    print(f"New internal session ID: {new_agent.internal_session.id}")
    
    # List checkpoints after rollback using the tool
    print("\n=== Listing checkpoints AFTER rollback (using tool) ===")
    print("User: List checkpoints")
    response = new_agent.run("List checkpoints")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Also check directly via repository
    print("\n=== Checking checkpoints via repository ===")
    checkpoints_after = new_agent.checkpoint_repo.get_by_internal_session(
        new_agent.internal_session.id,
        auto_only=False
    )
    
    print(f"Checkpoints for new internal session {new_agent.internal_session.id}:")
    checkpoint_names_after = []
    for cp in checkpoints_after:
        if not cp.is_auto:  # Only show manual checkpoints
            checkpoint_type = "manual"
            name = cp.checkpoint_name or "Unnamed"
            print(f"  - ID: {cp.id} | {name} | Type: {checkpoint_type}")
            checkpoint_names_after.append(name)
    
    # Test results
    print("\n=== TEST RESULTS ===")
    
    # Check if we have the expected checkpoints
    expected_checkpoints = ["A", "B"]  # After rolling back to B, we should have A and B
    
    # Check what checkpoints are visible after rollback
    if len(checkpoint_names_after) == 0:
        print("❌ FAILURE: No checkpoints visible after rollback!")
        print("   This indicates the system is NOT doing full snapshot rollback.")
        print("   Checkpoints are tied to internal_session_id and lost on rollback.")
    elif all(cp in " ".join(checkpoint_names_after) for cp in expected_checkpoints):
        print("✅ SUCCESS: Checkpoints A and B are preserved after rollback!")
        print("   The system correctly implements full snapshot rollback.")
    else:
        print(f"❌ FAILURE: Expected checkpoints {expected_checkpoints} but got {checkpoint_names_after}")
        print("   The system is not properly preserving checkpoints.")
    
    # Try to rollback to checkpoint A from the rolled-back state
    print("\n=== Testing nested rollback ===")
    print("User: Can you rollback to checkpoint A?")
    response = new_agent.run("Rollback to checkpoint A")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    response_text = str(response.content if hasattr(response, 'content') else response).lower()
    if "not found" in response_text or "no checkpoint" in response_text:
        print("\n❌ FAILURE: Cannot rollback to checkpoint A from rolled-back state")
        print("   This confirms checkpoints are lost after rollback.")
    elif "rollback" in response_text and "requested" in response_text:
        print("\n✅ SUCCESS: Can rollback to checkpoint A from rolled-back state")
        print("   Full snapshot rollback is working correctly.")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_checkpoint_preservation()