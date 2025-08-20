#!/usr/bin/env python3
"""
Conversation-driven tool test:
- Defines create_file/delete_file tools
- Prompts the agent in natural language to use the tool
- Prints the tool record BEFORE rollback
- Rolls back and verifies file deletion
- Redoes and verifies file recreation
"""

import os
import sys
from pathlib import Path
from time import sleep

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent_service import AgentService
from src.auth.auth_service import AuthService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository

sleep_n = 2 # SLEEP TIME FOR DEBUG

def create_file(path: str) -> dict:
    open(path, "w").close()
    return {"path": path}


def delete_file(args, result):
    file_path = result.get("path") if isinstance(result, dict) else None
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return None


def main():
    print("=== Conversation-driven Tool Test ===\n")

    # Login
    auth_service = AuthService()
    ok, user, _ = auth_service.login("rootusr", "1234")
    if not ok:
        print("Authentication failed")
        return

    # Session
    external_session_repo = ExternalSessionRepository()
    external_session = ExternalSession(user_id=user.id, session_name="Conversation Tool Test")
    external_session = external_session_repo.create(external_session)

    # Agent
    agent_service = AgentService()
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    agent = agent_service.create_new_agent(
        external_session_id=external_session.id,
        tools=[create_file],
        reverse_tools={"create_file": delete_file},
        base_url=base_url,
        api_key=api_key,
    )

    test_path = "conv_tool_file.txt"
    sleep(sleep_n)

    # Ask the agent in natural language
    print(f"User: Please create a text file named '{test_path}' using the available tools.")
    resp = agent.run(f"Create a file named {test_path} using the tools.")
    print(f"Assistant: {resp.content if hasattr(resp, 'content') else resp}")
    sleep(sleep_n)

    # Track before rollback
    track = agent.get_tool_track()
    print(f"\nRecorded tool invocations BEFORE rollback: {len(track)}")
    for rec in track:
        print(f"  - {rec.tool_name} args={{'path': '{rec.args.get('path')}'}} success={rec.success}")

    print(f"File exists before rollback: {os.path.exists(test_path)}")

    # Rollback  
    sleep(sleep_n)
    reverse_results = agent.rollback_tools()
    for rr in reverse_results:
        print(f"  - reversed {rr.tool_name}: success={rr.reversed_successfully} error={rr.error_message}")

    print(f"File exists after rollback: {os.path.exists(test_path)}")

    # Redo
    sleep(sleep_n)
    redo_results = agent.redo_tools()
    for r in redo_results:
        print(f"  - redo {r.tool_name}: success={r.success} error={r.error_message}")

    print(f"File exists after redo: {os.path.exists(test_path)}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    main()


