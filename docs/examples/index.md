# Examples and Tutorials

## Overview

This section provides practical examples and tutorials for using the Rollback Agent System in various scenarios.

## Basic Examples

### 1. Simple Conversation with Checkpoints

```python
#!/usr/bin/env python3
"""Basic example of using checkpoints in a conversation."""

from src.agents.agent_service import AgentService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository

def main():
    # Create external session
    repo = ExternalSessionRepository()
    session = ExternalSession(user_id=1, session_name="Learning Session")
    session = repo.create(session)
    
    # Create agent
    service = AgentService()
    agent = service.create_new_agent(session.id)
    
    # Initial conversation
    print("Starting conversation...")
    response = agent.run("Hello! I want to learn about Python lists.")
    print(f"Agent: {response.content}\n")
    
    # Create checkpoint before moving to advanced topic
    checkpoint_result = agent.create_checkpoint("basics-covered")
    print(f"Checkpoint: {checkpoint_result}\n")
    
    # Continue with advanced topic
    response = agent.run("Now explain list comprehensions in detail.")
    print(f"Agent: {response.content}\n")
    
    # User wants to go back
    response = agent.run("Actually, let's go back to where we were before list comprehensions.")
    print(f"Agent: {response.content}\n")
    
    # The system will handle the rollback
    if service.handle_agent_response(agent, response):
        checkpoint_id = agent.session_state.get('rollback_checkpoint_id')
        new_agent = service.rollback_to_checkpoint(session.id, checkpoint_id)
        print("Rolled back successfully!")
        
        # Continue from the checkpoint
        response = new_agent.run("Let's talk about tuples instead.")
        print(f"Agent: {response.content}\n")

if __name__ == "__main__":
    main()
```

### 2. Using Custom Tools with Auto-Checkpoints

```python
#!/usr/bin/env python3
"""Example of custom tools with automatic checkpointing."""

from agno.models.openai import OpenAIChat
from src.agents.rollback_agent import RollbackAgent
import json
import requests

def weather_tool(city: str) -> str:
    """Get current weather for a city (mock implementation)."""
    # In production, use a real weather API
    weather_data = {
        "London": "☁️ Cloudy, 15°C",
        "New York": "☀️ Sunny, 22°C",
        "Tokyo": "🌧️ Rainy, 18°C",
        "Paris": "⛅ Partly cloudy, 20°C"
    }
    return weather_data.get(city, f"Weather data not available for {city}")

def calculate_tool(expression: str) -> str:
    """Safely calculate a mathematical expression."""
    try:
        # In production, use a safer evaluation method
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "pow": pow
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating expression: {e}"

def json_formatter_tool(data: str, indent: int = 2) -> str:
    """Format JSON data for better readability."""
    try:
        parsed = json.loads(data)
        formatted = json.dumps(parsed, indent=indent, sort_keys=True)
        return f"Formatted JSON:\n{formatted}"
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

def main():
    # Create agent with custom tools
    model = OpenAIChat(id="gpt-4o-mini", temperature=0.7)
    
    agent = RollbackAgent(
        external_session_id=1,
        model=model,
        tools=[weather_tool, calculate_tool, json_formatter_tool],
        auto_checkpoint=True  # Automatically checkpoint after each tool use
    )
    
    print("Agent with custom tools initialized.\n")
    
    # Use weather tool (auto-checkpoint created)
    response = agent.run("What's the weather in London?")
    print(f"Agent: {response.content}\n")
    
    # Use calculator tool (another auto-checkpoint)
    response = agent.run("Calculate (100 + 50) * 2")
    print(f"Agent: {response.content}\n")
    
    # Use JSON formatter (another auto-checkpoint)
    json_data = '{"name": "John", "age": 30, "city": "New York"}'
    response = agent.run(f"Format this JSON: {json_data}")
    print(f"Agent: {response.content}\n")
    
    # List all checkpoints (including automatic ones)
    checkpoints = agent.list_checkpoints_tool()
    print(f"All checkpoints:\n{checkpoints}\n")
    
    # Clean up old auto-checkpoints
    cleanup_result = agent.cleanup_auto_checkpoints_tool(keep_latest=2)
    print(f"Cleanup: {cleanup_result}\n")

if __name__ == "__main__":
    main()
```

## Advanced Examples

### 3. Multi-User Session Management

```python
#!/usr/bin/env python3
"""Example of managing multiple users and their sessions."""

from src.auth.auth_service import AuthService
from src.agents.agent_service import AgentService
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.sessions.external_session import ExternalSession

class MultiUserSystem:
    def __init__(self):
        self.auth = AuthService()
        self.agent_service = AgentService()
        self.session_repo = ExternalSessionRepository()
        self.users = {}
        self.agents = {}
    
    def register_user(self, username: str, password: str):
        """Register a new user."""
        success, user, message = self.auth.register(username, password)
        if success:
            self.users[username] = user
            print(f"✓ User '{username}' registered successfully")
            return user
        else:
            print(f"✗ Registration failed: {message}")
            return None
    
    def create_user_session(self, username: str, session_name: str):
        """Create a new session for a user."""
        user = self.users.get(username)
        if not user:
            print(f"User '{username}' not found")
            return None
        
        # Create external session
        session = ExternalSession(
            user_id=user.id,
            session_name=session_name
        )
        session = self.session_repo.create(session)
        
        # Create agent for this session
        agent = self.agent_service.create_new_agent(session.id)
        
        # Store agent reference
        agent_key = f"{username}:{session_name}"
        self.agents[agent_key] = agent
        
        print(f"✓ Session '{session_name}' created for user '{username}'")
        return agent
    
    def get_user_agent(self, username: str, session_name: str):
        """Get the agent for a user's session."""
        agent_key = f"{username}:{session_name}"
        return self.agents.get(agent_key)
    
    def list_user_sessions(self, username: str):
        """List all sessions for a user."""
        user = self.users.get(username)
        if not user:
            return []
        
        sessions = self.session_repo.get_user_sessions(user.id)
        return sessions

def main():
    system = MultiUserSystem()
    
    # Register multiple users
    alice = system.register_user("alice", "alice123")
    bob = system.register_user("bob", "bob456")
    
    # Create sessions for Alice
    alice_python = system.create_user_session("alice", "Learning Python")
    alice_ml = system.create_user_session("alice", "Machine Learning")
    
    # Create session for Bob
    bob_webdev = system.create_user_session("bob", "Web Development")
    
    # Alice uses her Python session
    if alice_python:
        print("\n--- Alice's Python Session ---")
        response = alice_python.run("Teach me about Python decorators")
        print(f"Agent: {response.content[:100]}...")
        
        alice_python.create_checkpoint("decorators-explained")
    
    # Bob uses his session
    if bob_webdev:
        print("\n--- Bob's Web Dev Session ---")
        response = bob_webdev.run("Explain REST APIs")
        print(f"Agent: {response.content[:100]}...")
    
    # List Alice's sessions
    print("\n--- Alice's Sessions ---")
    alice_sessions = system.list_user_sessions("alice")
    for session in alice_sessions:
        print(f"- {session.session_name} (ID: {session.id})")

if __name__ == "__main__":
    main()
```

### 4. Conversation Branching Example

```python
#!/usr/bin/env python3
"""Example of creating multiple conversation branches from checkpoints."""

from src.agents.agent_service import AgentService
from src.database.repositories.checkpoint_repository import CheckpointRepository

class ConversationBrancher:
    def __init__(self, external_session_id: int):
        self.external_session_id = external_session_id
        self.service = AgentService()
        self.checkpoint_repo = CheckpointRepository()
        self.branches = {}
    
    def create_main_branch(self):
        """Create the main conversation branch."""
        agent = self.service.create_new_agent(self.external_session_id)
        self.branches['main'] = agent
        return agent
    
    def create_checkpoint(self, branch_name: str, checkpoint_name: str):
        """Create a checkpoint in a branch."""
        agent = self.branches.get(branch_name)
        if agent:
            result = agent.create_checkpoint(checkpoint_name)
            print(f"Branch '{branch_name}': {result}")
            return result
    
    def branch_from_checkpoint(self, checkpoint_id: int, new_branch_name: str):
        """Create a new branch from a checkpoint."""
        new_agent = self.service.rollback_to_checkpoint(
            self.external_session_id,
            checkpoint_id
        )
        if new_agent:
            self.branches[new_branch_name] = new_agent
            print(f"✓ Created branch '{new_branch_name}' from checkpoint {checkpoint_id}")
        return new_agent
    
    def continue_branch(self, branch_name: str, message: str):
        """Continue conversation in a specific branch."""
        agent = self.branches.get(branch_name)
        if agent:
            response = agent.run(message)
            return response
        return None

def main():
    # Initialize brancher
    brancher = ConversationBrancher(external_session_id=1)
    
    # Create main branch
    print("=== Creating Main Branch ===")
    main_agent = brancher.create_main_branch()
    
    # Initial conversation
    response = main_agent.run("Let's discuss machine learning algorithms")
    print(f"Main: {response.content[:150]}...\n")
    
    # Create checkpoint before branching
    brancher.create_checkpoint('main', 'ml-intro')
    
    # Get checkpoint ID (in real app, you'd track this)
    checkpoints = main_agent.list_checkpoints_tool()
    # Parse checkpoint ID from the output (simplified for example)
    checkpoint_id = 1  # Assuming this is our checkpoint
    
    # Continue main branch with technical discussion
    print("\n=== Main Branch: Technical Path ===")
    response = brancher.continue_branch('main', 
        "Explain the mathematics behind neural networks in detail")
    print(f"Main (Technical): {response.content[:150]}...\n")
    
    # Create alternative branch for simpler explanation
    print("\n=== Creating Simple Branch ===")
    simple_agent = brancher.branch_from_checkpoint(checkpoint_id, 'simple')
    
    # Continue simple branch with beginner-friendly discussion
    response = brancher.continue_branch('simple',
        "Explain neural networks using simple analogies without math")
    print(f"Simple Branch: {response.content[:150]}...\n")
    
    # Create another branch for practical examples
    print("\n=== Creating Practical Branch ===")
    practical_agent = brancher.branch_from_checkpoint(checkpoint_id, 'practical')
    
    response = brancher.continue_branch('practical',
        "Show me practical code examples of implementing neural networks")
    print(f"Practical Branch: {response.content[:150]}...\n")
    
    # Summary of branches
    print("\n=== Branch Summary ===")
    for branch_name in brancher.branches:
        print(f"- Branch '{branch_name}' is available")

if __name__ == "__main__":
    main()
```

### 5. Automated Testing with Rollback

```python
#!/usr/bin/env python3
"""Example of using rollback for automated testing scenarios."""

from typing import List, Tuple
from src.agents.agent_service import AgentService

class ConversationTester:
    def __init__(self, external_session_id: int):
        self.service = AgentService()
        self.external_session_id = external_session_id
        self.test_results = []
    
    def run_test_scenario(self, 
                         scenario_name: str,
                         test_messages: List[str],
                         expected_keywords: List[List[str]]) -> bool:
        """Run a test scenario and check for expected keywords in responses."""
        
        print(f"\n=== Testing Scenario: {scenario_name} ===")
        
        # Create fresh agent for test
        agent = self.service.create_new_agent(self.external_session_id)
        
        # Create initial checkpoint
        agent.create_checkpoint(f"{scenario_name}_start")
        
        all_passed = True
        
        for i, (message, keywords) in enumerate(zip(test_messages, expected_keywords)):
            print(f"\nTest {i+1}: {message}")
            
            # Send message
            response = agent.run(message)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Check for expected keywords
            found_keywords = [kw for kw in keywords if kw.lower() in response_text.lower()]
            passed = len(found_keywords) == len(keywords)
            
            if passed:
                print(f"✓ Passed - Found all keywords: {keywords}")
            else:
                print(f"✗ Failed - Missing keywords: {set(keywords) - set(found_keywords)}")
                all_passed = False
            
            # Create checkpoint after each test
            agent.create_checkpoint(f"{scenario_name}_test_{i+1}")
        
        # Store results
        self.test_results.append({
            'scenario': scenario_name,
            'passed': all_passed,
            'tests_run': len(test_messages)
        })
        
        return all_passed
    
    def run_regression_test(self, checkpoint_id: int, 
                           regression_messages: List[Tuple[str, List[str]]]) -> bool:
        """Run regression tests from a specific checkpoint."""
        
        print(f"\n=== Regression Testing from Checkpoint {checkpoint_id} ===")
        
        all_passed = True
        
        for message, expected_keywords in regression_messages:
            # Rollback to checkpoint for each test
            agent = self.service.rollback_to_checkpoint(
                self.external_session_id,
                checkpoint_id
            )
            
            if not agent:
                print(f"✗ Failed to rollback to checkpoint {checkpoint_id}")
                return False
            
            # Run test
            response = agent.run(message)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Check keywords
            found = all(kw.lower() in response_text.lower() for kw in expected_keywords)
            
            if found:
                print(f"✓ Regression test passed: {message[:50]}...")
            else:
                print(f"✗ Regression test failed: {message[:50]}...")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        for result in self.test_results:
            status = "PASSED" if result['passed'] else "FAILED"
            print(f"{result['scenario']}: {status} ({result['tests_run']} tests)")

def main():
    tester = ConversationTester(external_session_id=1)
    
    # Test Scenario 1: Basic Math
    tester.run_test_scenario(
        "Basic Math",
        [
            "What is 2 + 2?",
            "What is 10 * 5?",
            "What is 100 divided by 4?"
        ],
        [
            ["4", "four"],
            ["50", "fifty"],
            ["25", "twenty-five"]
        ]
    )
    
    # Test Scenario 2: Python Basics
    tester.run_test_scenario(
        "Python Basics",
        [
            "What is a Python list?",
            "How do I create a function in Python?",
            "What are Python decorators?"
        ],
        [
            ["list", "collection", "ordered"],
            ["def", "function", "parameters"],
            ["decorator", "@", "wrapper"]
        ]
    )
    
    # Run regression tests from a checkpoint
    # (Assuming checkpoint 1 exists from previous tests)
    tester.run_regression_test(
        1,
        [
            ("Explain variables", ["variable", "store", "value"]),
            ("What are data types?", ["type", "integer", "string"])
        ]
    )
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()
```

## Tutorial: Building a Learning Assistant

### Step 1: Setup

```python
# setup.py
import os
from src.auth.auth_service import AuthService
from src.database.repositories.user_repository import UserRepository

def setup_system():
    """Initialize the system with default admin user."""
    
    # Ensure database directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create admin user if not exists
    auth = AuthService()
    user_repo = UserRepository()
    
    if not user_repo.get_by_username("admin"):
        success, user, message = auth.register("admin", "admin123")
        if success:
            user.is_admin = True
            user_repo.update(user)
            print("✓ Admin user created")
    
    print("✓ System ready")

if __name__ == "__main__":
    setup_system()
```

### Step 2: Create Learning Assistant

```python
# learning_assistant.py
from typing import Dict, List, Optional
from src.agents.rollback_agent import RollbackAgent
from agno.models.openai import OpenAIChat

class LearningAssistant:
    """An intelligent learning assistant with progress tracking."""
    
    def __init__(self, external_session_id: int, subject: str):
        self.subject = subject
        self.model = OpenAIChat(id="gpt-4o-mini", temperature=0.7)
        
        # Create agent with learning tools
        self.agent = RollbackAgent(
            external_session_id=external_session_id,
            model=self.model,
            tools=[
                self.quiz_tool,
                self.explain_tool,
                self.example_tool
            ],
            auto_checkpoint=True
        )
        
        self.topics_covered = []
        self.quiz_scores = []
    
    def quiz_tool(self, topic: str, difficulty: str = "medium") -> str:
        """Generate a quiz question on a topic."""
        # In production, implement actual quiz generation
        return f"Quiz on {topic} (Difficulty: {difficulty}): [Question would appear here]"
    
    def explain_tool(self, concept: str, level: str = "intermediate") -> str:
        """Explain a concept at specified level."""
        return f"Explaining {concept} at {level} level: [Explanation would appear here]"
    
    def example_tool(self, topic: str, num_examples: int = 3) -> str:
        """Provide examples for a topic."""
        return f"Here are {num_examples} examples for {topic}: [Examples would appear here]"
    
    def start_lesson(self, topic: str):
        """Start a new lesson on a topic."""
        # Create checkpoint before new topic
        self.agent.create_checkpoint(f"before_{topic}")
        
        # Introduction
        response = self.agent.run(
            f"Let's learn about {topic} in {self.subject}. "
            f"Start with an overview suitable for beginners."
        )
        
        self.topics_covered.append(topic)
        return response
    
    def practice_topic(self, topic: str):
        """Practice a topic with examples and exercises."""
        response = self.agent.run(
            f"Let's practice {topic} with some examples and exercises."
        )
        return response
    
    def review_progress(self) -> str:
        """Review learning progress."""
        topics_str = ", ".join(self.topics_covered)
        response = self.agent.run(
            f"Let's review what we've learned. "
            f"Topics covered: {topics_str}. "
            f"Provide a summary of key points."
        )
        return response
    
    def rollback_to_topic(self, topic: str):
        """Rollback to the beginning of a specific topic."""
        response = self.agent.run(
            f"Let's go back to before we started learning about {topic}"
        )
        return response

# Usage example
def main():
    assistant = LearningAssistant(
        external_session_id=1,
        subject="Python Programming"
    )
    
    # Start first lesson
    print("=== Lesson 1: Variables ===")
    response = assistant.start_lesson("variables")
    print(response.content[:200] + "...\n")
    
    # Practice
    print("=== Practice ===")
    response = assistant.practice_topic("variables")
    print(response.content[:200] + "...\n")
    
    # Move to next topic
    print("=== Lesson 2: Functions ===")
    response = assistant.start_lesson("functions")
    print(response.content[:200] + "...\n")
    
    # Review progress
    print("=== Progress Review ===")
    summary = assistant.review_progress()
    print(summary.content[:200] + "...\n")
    
    # Go back if needed
    print("=== Rolling Back ===")
    response = assistant.rollback_to_topic("functions")
    print("Rolled back to before functions lesson\n")

if __name__ == "__main__":
    main()
```

## Best Practices

1. **Always create checkpoints before significant changes**
2. **Use descriptive checkpoint names**
3. **Clean up automatic checkpoints periodically**
4. **Test rollback functionality regularly**
5. **Monitor session proliferation**
6. **Implement proper error handling**
7. **Use type hints for better code maintainability**

## Next Steps

- [CLI Guide](../cli/index.md) - Master the CLI interface
- [API Reference](../api/index.md) - Detailed API documentation
- [Architecture](../architecture/overview.md) - System design details