#!/usr/bin/env python3
"""
Test script to verify automatic checkpoint creation with custom tools.
"""

import os
import sys
from pathlib import Path
from time import sleep

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent_service import AgentService
from src.auth.auth_service import AuthService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository

sleep_n = 2 # SLEEP TIME FOR DEBUG

def create_file(path: str) -> dict:
    """Create an empty file and return its path."""
    open(path, "w").close()
    return {"path": path}

def delete_file(args, result):
    """Reverse handler to delete the created file if it exists."""
    import os as _os
    file_path = result.get("path") if isinstance(result, dict) else None
    if file_path and _os.path.exists(file_path):
        _os.remove(file_path)
    return None

def main():
    """Test automatic checkpoint creation."""
    
    print("=== Testing Automatic Checkpoints with Custom Tools ===\n")
    
    # Authenticate
    auth_service = AuthService()
    success, user, _ = auth_service.login("rootusr", "1234")
    if not success:
        print("Authentication failed")
        return
    
    # Create session
    external_session_repo = ExternalSessionRepository()
    external_session = ExternalSession(
        user_id=user.id,
        session_name="Auto Checkpoint Test"
    )
    external_session = external_session_repo.create(external_session)
    
    # Create agent with custom tool
    agent_service = AgentService()

    # Read model connection settings (align with test_key.py)
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    agent = agent_service.create_new_agent(
        external_session_id=external_session.id,
        tools=[create_file],
        reverse_tools={"create_file": delete_file},
        base_url=base_url,
        api_key=api_key
        # show_tool_calls=True is already set by default in agent_service
    )
    
    print("Agent created with custom calculator tool\n")
    sleep(sleep_n)
    
    # Initial checkpoint count
    initial_checkpoints = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    print(f"Initial checkpoints: {len(initial_checkpoints)}")
    
    # Test 1: Use custom tool to create a file
    test_path = "tmp_test_file.txt"
    print("\nTest 1: Using custom tool to create a file")
    print(f"User: Create file at {test_path}")
    response = agent.run(f"Use the create_file tool to create {test_path}")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    sleep(sleep_n)
    
    # Check if response has tool_calls attribute
    print(f"\nResponse has tool_calls: {hasattr(response, 'tool_calls')}")
    if hasattr(response, 'tool_calls'):
        print(f"Tool calls: {response.tool_calls}")
    
    # Show recorded tool invocations (from rollback registry) BEFORE rollback
    try:
        track = agent.get_tool_track()
        print(f"\nRecorded tool invocations: {len(track)}")
        for rec in track:
            print(f"  - {rec.tool_name} args={rec.args} success={rec.success}")
    except Exception as e:
        print(f"Could not read tool track: {e}")

    # Check checkpoints after custom tool
    checkpoints_after_custom = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    print(f"\nCheckpoints after custom tool: {len(checkpoints_after_custom)}")
    
    # Test 2: Use checkpoint tool
    print("\nTest 2: Using checkpoint tool")
    print("User: Create checkpoint 'Test'")
    response = agent.run("Create checkpoint 'Test'")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Check checkpoints after checkpoint tool
    checkpoints_after_checkpoint = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    print(f"\nCheckpoints after checkpoint tool: {len(checkpoints_after_checkpoint)}")
    
    # Verify file exists before rollback
    print(f"\nFile exists before rollback: {os.path.exists(test_path)}")

    # Optionally demonstrate tool rollback (reverse handlers)
    print("\nAttempting to rollback recorded tool effects...")
    sleep(sleep_n)
    try:
        reverse_results = agent.rollback_tools()
        for rr in reverse_results:
            print(f"  - reversed {rr.tool_name}: success={rr.reversed_successfully} error={rr.error_message}")
    except Exception as e:
        print(f"Rollback failed: {e}")

    # Verify file removed after rollback
    print(f"File exists after rollback: {os.path.exists(test_path)}")

    # Demonstrate redo (recreate the file via forward tool replay)
    try:
        sleep(sleep_n)
        redo_results = agent.redo_tools()
        for rr in redo_results:
            print(f"  - redo {rr.tool_name}: success={rr.success} error={rr.error_message}")
    except Exception as e:
        print(f"Redo failed: {e}")

    # Verify file re-created after redo
    print(f"File exists after redo: {os.path.exists(test_path)}")



if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    main()