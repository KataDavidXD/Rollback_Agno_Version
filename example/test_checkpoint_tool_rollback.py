#!/usr/bin/env python3
"""
Test script demonstrating checkpoint + tool rollback integration.

This script:
1. Creates files using tools
2. Creates a checkpoint
3. Creates more files using tools
4. Rolls back to the checkpoint (automatically reverses tools created after checkpoint)
5. Verifies file states
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


def create_file(path: str) -> dict:
    """Create an empty file and return its path."""
    open(path, "w").close()
    print(f"Created file: {path}")
    return {"path": path}


def delete_file(args, result):
    """Reverse handler to delete the created file if it exists."""
    file_path = result.get("path") if isinstance(result, dict) else None
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    return None


def write_text_file(path: str, content: str) -> dict:
    """Write content to a file and return its path."""
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote to file: {path}")
    return {"path": path, "content": content}


def delete_text_file(args, result):
    """Reverse handler to delete the written file if it exists."""
    file_path = result.get("path") if isinstance(result, dict) else None
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted text file: {file_path}")
    return None


def check_files_exist(file_paths):
    """Check which files exist."""
    print("\nFile existence check:")
    for path in file_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}")
    return [path for path in file_paths if os.path.exists(path)]


def main():
    """Test checkpoint + tool rollback integration."""
    
    print("=== Testing Checkpoint + Tool Rollback Integration ===\n")
    
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
        session_name="Checkpoint Tool Rollback Test"
    )
    external_session = external_session_repo.create(external_session)
    
    # Create agent with file tools
    agent_service = AgentService()
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    agent = agent_service.create_new_agent(
        external_session_id=external_session.id,
        tools=[create_file, write_text_file],
        reverse_tools={
            "create_file": delete_file,
            "write_text_file": delete_text_file
        },
        base_url=base_url,
        api_key=api_key
    )
    
    print("Agent created with file creation tools\n")
    sleep(0.5)
    
    # Phase 1: Create some files BEFORE checkpoint
    print("=== Phase 1: Creating files before checkpoint ===")
    
    # Create first file
    print("User: Create file 'before1.txt'")
    response1 = agent.run("Create a file named 'before1.txt' using the create_file tool")
    print(f"Assistant: {response1.content if hasattr(response1, 'content') else response1}")
    sleep(0.5)
    
    # Write to second file
    print("\nUser: Write 'Hello World' to 'before2.txt'")
    response2 = agent.run("Write 'Hello World' to file 'before2.txt' using the write_text_file tool")
    print(f"Assistant: {response2.content if hasattr(response2, 'content') else response2}")
    sleep(0.5)
    
    # Show tool track before checkpoint
    track_before_checkpoint = agent.get_tool_track()
    print(f"\nTool track before checkpoint: {len(track_before_checkpoint)} operations")
    for i, rec in enumerate(track_before_checkpoint):
        print(f"  {i}: {rec.tool_name} args={rec.args} success={rec.success}")
    
    # Create checkpoint
    print("\n=== Creating Checkpoint ===")
    print("User: Create checkpoint 'Before Phase 2'")
    response3 = agent.run("Create a checkpoint called 'Before Phase 2'")
    print(f"Assistant: {response3.content if hasattr(response3, 'content') else response3}")
    sleep(0.5)
    
    # Get checkpoint ID from the response or list checkpoints
    checkpoints = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    checkpoint_id = None
    for cp in checkpoints:
        if cp.checkpoint_name and "Before Phase 2" in cp.checkpoint_name:
            checkpoint_id = cp.id
            print(f"Found checkpoint ID: {checkpoint_id}")
            break
    
    if not checkpoint_id:
        print("ERROR: Could not find checkpoint ID")
        return
    
    # Phase 2: Create more files AFTER checkpoint
    print("\n=== Phase 2: Creating files after checkpoint ===")
    
    # Create third file
    print("User: Create file 'after1.txt'")
    response4 = agent.run("Create a file named 'after1.txt' using the create_file tool")
    print(f"Assistant: {response4.content if hasattr(response4, 'content') else response4}")
    sleep(0.5)
    
    # Write to fourth file
    print("\nUser: Write 'After checkpoint' to 'after2.txt'")
    response5 = agent.run("Write 'After checkpoint' to file 'after2.txt' using the write_text_file tool")
    print(f"Assistant: {response5.content if hasattr(response5, 'content') else response5}")
    sleep(0.5)
    
    # Show complete tool track
    track_after_phase2 = agent.get_tool_track()
    print(f"\nComplete tool track after phase 2: {len(track_after_phase2)} operations")
    for i, rec in enumerate(track_after_phase2):
        print(f"  {i}: {rec.tool_name} args={rec.args} success={rec.success}")
    
    # Check file states before rollback
    all_files = ['before1.txt', 'before2.txt', 'after1.txt', 'after2.txt']
    print("\n=== Before Rollback ===")
    existing_files = check_files_exist(all_files)
    
    # Rollback to checkpoint (should automatically reverse tools created after checkpoint)
    print(f"\n=== Rolling back to checkpoint {checkpoint_id} ===")
    print("This should automatically reverse tool operations created after the checkpoint...")
    sleep(1)
    
    new_agent = agent_service.rollback_to_checkpoint(
        external_session.id,
        checkpoint_id,
        rollback_tools=True  # Enable automatic tool rollback
    )
    
    if not new_agent:
        print("ERROR: Rollback failed")
        return
    
    print("Rollback completed!")
    sleep(0.5)
    
    # Check file states after rollback
    print("\n=== After Rollback ===")
    remaining_files = check_files_exist(all_files)
    
    # Verify expected behavior
    print("\n=== Verification ===")
    expected_remaining = ['before1.txt', 'before2.txt']  # Files created before checkpoint
    expected_removed = ['after1.txt', 'after2.txt']     # Files created after checkpoint
    
    success = True
    for file in expected_remaining:
        if file in remaining_files:
            print(f"✅ {file} correctly preserved (created before checkpoint)")
        else:
            print(f"❌ {file} incorrectly removed (should be preserved)")
            success = False
    
    for file in expected_removed:
        if file not in remaining_files:
            print(f"✅ {file} correctly removed (created after checkpoint)")
        else:
            print(f"❌ {file} incorrectly preserved (should be removed)")
            success = False
    
    # Show new agent's tool track (should only have operations up to checkpoint)
    new_track = new_agent.get_tool_track()
    print(f"\nNew agent tool track: {len(new_track)} operations")
    for i, rec in enumerate(new_track):
        print(f"  {i}: {rec.tool_name} args={rec.args} success={rec.success}")
    
    if success:
        print("\n🎉 SUCCESS: Checkpoint + Tool Rollback integration working correctly!")
    else:
        print("\n❌ FAILURE: Checkpoint + Tool Rollback integration has issues")
    
    # Cleanup remaining files
    print("\n=== Cleanup ===")
    for file in remaining_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up: {file}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    main()
