# Quick Start Guide

This guide will help you get started with the Rollback Agent System in minutes.

## Basic Usage

### 1. Simple Conversation with Checkpoints

```python
from src.agents.agent_service import AgentService
from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository

# Create an external session
repo = ExternalSessionRepository()
session = ExternalSession(user_id=1, session_name="My First Session")
session = repo.create(session)

# Create agent service and agent
service = AgentService()
agent = service.create_new_agent(session.id)

# Have a conversation
response = agent.run("Hello! I'm learning Python.")
print(response.content)

# Create a checkpoint
agent.create_checkpoint("before-advanced-topics")

# Continue conversation
response = agent.run("Now explain decorators in Python.")
print(response.content)

# Rollback if needed
response = agent.run("Actually, rollback to before-advanced-topics")
# System creates new session from checkpoint
```

### 2. Using the CLI Interface

The easiest way to interact with the system is through the CLI:

```bash
python example/advanced_cli.py
```

#### CLI Workflow

1. **Register/Login**
   ```
   Choose: Register
   Username: your_username
   Password: ********
   ```

2. **Create Session**
   ```
   Main Menu > Session Management > Create New Session
   Name: "Learning Python"
   ```

3. **Start Chatting**
   ```
   Commands:
   /checkpoint <name>  - Save current state
   /rollback <id>      - Restore to checkpoint
   /checkpoints        - List all checkpoints
   /history           - Show conversation
   ```

### 3. Custom Tools Integration

Add your own tools to the agent:

```python
from src.agents.rollback_agent import RollbackAgent
from agno.models.openai import OpenAIChat

def calculate_tool(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except:
        return "Invalid expression"

def weather_tool(city: str) -> str:
    """Get weather for a city (mock)."""
    return f"Weather in {city}: Sunny, 22°C"

# Create agent with custom tools
model = OpenAIChat(id="gpt-4o-mini")
agent = RollbackAgent(
    external_session_id=1,
    model=model,
    tools=[calculate_tool, weather_tool],
    auto_checkpoint=True  # Auto-checkpoint after tool use
)

# Use the tools
agent.run("What's 25 * 4?")  # Auto-checkpoint created
agent.run("What's the weather in London?")  # Another auto-checkpoint
```

## Key Concepts

### Sessions Hierarchy

```
External Session (User's Project)
    ├── Internal Session 1 (Conversation Branch)
    │   ├── Checkpoint A
    │   ├── Checkpoint B (auto)
    │   └── Checkpoint C
    └── Internal Session 2 (After Rollback)
        ├── Checkpoint A (copied)
        └── Checkpoint D (new)
```

### Checkpoint Types

1. **Manual Checkpoints** - Created explicitly by user
   ```python
   agent.create_checkpoint("important-state")
   ```

2. **Automatic Checkpoints** - Created after tool calls
   ```python
   # Automatically created when tools are used
   agent.run("Calculate 5 + 3")  # If calculate tool exists
   ```

### Rollback Behavior

When you rollback:
1. A new internal session is created
2. State is restored from the checkpoint
3. Conversation history is preserved
4. Previous checkpoints are available

## Common Patterns

### Pattern 1: Exploratory Conversations

```python
# Save before trying something new
agent.create_checkpoint("safe-point")

# Explore a complex topic
agent.run("Explain quantum computing")
agent.run("How does superposition work?")

# Not satisfied? Rollback
agent.run("Rollback to safe-point")

# Try a different approach
agent.run("Explain quantum computing with simple analogies")
```

### Pattern 2: Progressive Learning

```python
# Learn step by step with checkpoints
agent.run("Teach me Python basics")
agent.create_checkpoint("basics-done")

agent.run("Now teach me functions")
agent.create_checkpoint("functions-done")

agent.run("Now teach me classes")
# Can always go back to any checkpoint
```

### Pattern 3: Tool Testing

```python
# Test different approaches
agent.run("Analyze this data: [1,2,3,4,5]")
checkpoint_id = agent.create_checkpoint("after-analysis")

agent.run("Now sort it descending")
# Don't like the result?

agent.rollback_to_checkpoint_tool(checkpoint_id)
agent.run("Calculate the mean instead")
```

## Advanced Features

### Session Branching

Create multiple paths from the same checkpoint:

```python
# Create checkpoint
checkpoint = agent.create_checkpoint("branch-point")

# Path 1
agent.run("Explain in technical terms")
session1_id = agent.internal_session.id

# Rollback and try path 2
new_agent = service.rollback_to_checkpoint(
    external_session_id, 
    checkpoint.id
)
new_agent.run("Explain in simple terms")
session2_id = new_agent.internal_session.id

# Now you have two different conversation branches
```

### Checkpoint Management

```python
# List all checkpoints
checkpoints = agent.list_checkpoints_tool()
print(checkpoints)

# Get checkpoint details
info = agent.get_checkpoint_info_tool(checkpoint_id=5)
print(info)

# Clean up old auto-checkpoints
agent.cleanup_auto_checkpoints_tool(keep_latest=3)

# Delete specific checkpoint
agent.delete_checkpoint_tool(checkpoint_id=10)
```

## Best Practices

1. **Name Checkpoints Meaningfully**
   ```python
   agent.create_checkpoint("before-code-generation")
   agent.create_checkpoint("working-solution-v1")
   ```

2. **Use Auto-checkpoints Wisely**
   - Enable for tool-heavy workflows
   - Disable for simple conversations
   - Clean up periodically

3. **Manage Session Proliferation**
   - Delete old sessions regularly
   - Use descriptive session names
   - Archive important conversations

## What's Next?

- [Architecture Overview](../architecture/overview.md) - Understand system internals
- [API Reference](../api/index.md) - Detailed API documentation
- [CLI Guide](../cli/index.md) - Master the CLI interface
- [Examples](../examples/index.md) - More code examples