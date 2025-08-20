#!/usr/bin/env python3
"""
Test script to verify automatic checkpoint creation with custom tools.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent_service import AgentService
from src.auth.auth_service import AuthService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository
from agno.tools.baidusearch import BaiduSearchTools

def simple_calculator(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


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
        tools=[BaiduSearchTools()],
        description="You are a search agent that helps users find the most relevant information using Baidu.",
        instructions=[
            "Given a topic by the user, respond with the 3 most relevant search results about that topic.",
            "Search for 5 results and select the top 3 unique items.",
            "Search in both English and Chinese.",
        ],
        base_url=base_url,
        api_key=api_key
        # show_tool_calls=True is already set by default in agent_service
    )
    
    print("Agent created with custom Baidu search tool\n")
    
    # Initial checkpoint count
    initial_checkpoints = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    print(f"Initial checkpoints: {len(initial_checkpoints)}")
    
    # Test 1: Use custom tool
    print("\nTest 1: Using custom tool")
    print("User: What is the weather in Beijing?")
    response = agent.run("What is the weather in Beijing?")
    print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
    
    # Check if response has tool_calls attribute
    print(f"\nResponse has tool_calls: {hasattr(response, 'tool_calls')}")
    if hasattr(response, 'tool_calls'):
        print(f"Tool calls: {response.tool_calls}")
    
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
    
    # List all checkpoints with details
    print("\n=== All Checkpoints ===")
    all_checkpoints = agent.checkpoint_repo.get_by_internal_session(
        agent.internal_session.id,
        auto_only=False
    )
    
    for cp in all_checkpoints:
        checkpoint_type = "AUTO" if cp.is_auto else "MANUAL"
        name = cp.checkpoint_name or "Unnamed"
        print(f"  [{checkpoint_type}] ID: {cp.id} | {name}")
    
    # Summary
    auto_count = sum(1 for cp in all_checkpoints if cp.is_auto)
    manual_count = sum(1 for cp in all_checkpoints if not cp.is_auto)
    
    print(f"\nSummary:")
    print(f"  Automatic checkpoints: {auto_count}")
    print(f"  Manual checkpoints: {manual_count}")
    print(f"  Total: {len(all_checkpoints)}")
    
    if auto_count == 0:
        print("\n❌ ISSUE: No automatic checkpoints created after custom tool use!")
        print("   This needs to be fixed for proper rollback functionality.")
    else:
        print("\n✅ SUCCESS: Automatic checkpoints are being created!")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    main()