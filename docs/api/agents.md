# Agent API Reference

## RollbackAgent

The core agent class that extends Agno's Agent with checkpoint and rollback capabilities.

### Class Definition

```python
class RollbackAgent(Agent):
    def __init__(
        self,
        external_session_id: int,
        model,
        auto_checkpoint: bool = True,
        internal_session_repo=None,
        checkpoint_repo=None,
        skip_session_creation: bool = False,
        **kwargs
    )
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `external_session_id` | `int` | Required | ID of the external session |
| `model` | `AgnoModel` | Required | The Agno model instance (e.g., OpenAIChat) |
| `auto_checkpoint` | `bool` | `True` | Enable automatic checkpointing after tool calls |
| `internal_session_repo` | `Repository` | `None` | Repository for internal session operations |
| `checkpoint_repo` | `Repository` | `None` | Repository for checkpoint operations |
| `skip_session_creation` | `bool` | `False` | Skip creating new internal session (for resume/rollback) |
| `**kwargs` | `Dict` | `{}` | Additional arguments passed to Agno Agent |

### Methods

#### run(message: str, **kwargs) -> Any

Process a user message and return the agent's response.

```python
response = agent.run("Explain Python decorators")
print(response.content)
```

**Parameters:**
- `message` (str): The user message to process
- `**kwargs`: Additional arguments for the run

**Returns:**
- Agent response object with content

**Side Effects:**
- Updates conversation history
- Creates automatic checkpoint if tools were used
- Saves session state to database

#### create_checkpoint(name: Optional[str] = None) -> str

Create a manual checkpoint of the current conversation state.

```python
result = agent.create_checkpoint("before-complex-topic")
# Returns: "✓ Checkpoint 'before-complex-topic' created successfully (ID: 5)"
```

**Parameters:**
- `name` (Optional[str]): Name for the checkpoint. If None, uses timestamp

**Returns:**
- Success message with checkpoint ID

#### list_checkpoints_tool() -> str

List all available checkpoints for the current session.

```python
checkpoints = agent.list_checkpoints_tool()
print(checkpoints)
# Available checkpoints:
# • ID: 1 | Initial state | Type: manual | Created: 2024-01-15 10:00:00
# • ID: 2 | After calculate_tool | Type: auto | Created: 2024-01-15 10:05:00
```

**Returns:**
- Formatted string listing all checkpoints

#### rollback_to_checkpoint_tool(checkpoint_id_or_name) -> str

Request rollback to a specific checkpoint.

```python
result = agent.rollback_to_checkpoint_tool("before-complex-topic")
# Or by ID:
result = agent.rollback_to_checkpoint_tool(5)
```

**Parameters:**
- `checkpoint_id_or_name`: Integer ID or string name of checkpoint

**Returns:**
- Message indicating rollback request status

**Note:** This marks a rollback request. The actual rollback must be handled by AgentService.

#### delete_checkpoint_tool(checkpoint_id: int) -> str

Delete a specific checkpoint.

```python
result = agent.delete_checkpoint_tool(10)
# Returns: "✓ Checkpoint 10 deleted successfully."
```

**Parameters:**
- `checkpoint_id` (int): ID of checkpoint to delete

**Returns:**
- Success or error message

#### get_checkpoint_info_tool(checkpoint_id: int) -> str

Get detailed information about a checkpoint.

```python
info = agent.get_checkpoint_info_tool(5)
print(info)
# Checkpoint Details:
# • ID: 5
# • Name: before-complex-topic
# • Type: Manual
# • Created: 2024-01-15 10:30:00
# • Conversation Length: 10 messages
```

**Parameters:**
- `checkpoint_id` (int): ID of checkpoint to inspect

**Returns:**
- Formatted checkpoint details

#### cleanup_auto_checkpoints_tool(keep_latest: int = 5) -> str

Clean up old automatic checkpoints.

```python
result = agent.cleanup_auto_checkpoints_tool(keep_latest=3)
# Returns: "✓ Cleaned up 7 old automatic checkpoints. Kept the latest 3."
```

**Parameters:**
- `keep_latest` (int): Number of latest auto checkpoints to keep

**Returns:**
- Cleanup summary message

#### get_conversation_history() -> List[Dict[str, Any]]

Get the full conversation history.

```python
history = agent.get_conversation_history()
for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

**Returns:**
- List of message dictionaries with 'role' and 'content'

#### get_session_state() -> Dict[str, Any]

Get the current session state.

```python
state = agent.get_session_state()
print(state)
# {'context': 'learning_python', 'level': 'beginner', ...}
```

**Returns:**
- Dictionary containing session state

### Class Methods

#### from_checkpoint(cls, checkpoint_id: int, ...) -> RollbackAgent

Create a new agent from a checkpoint (static method).

```python
restored_agent = RollbackAgent.from_checkpoint(
    checkpoint_id=5,
    external_session_id=1,
    model=model,
    checkpoint_repo=checkpoint_repo,
    internal_session_repo=internal_session_repo
)
```

**Parameters:**
- `checkpoint_id` (int): ID of checkpoint to restore from
- `external_session_id` (int): ID of external session
- `model`: Agno model instance
- `checkpoint_repo`: Checkpoint repository
- `internal_session_repo`: Internal session repository
- `**kwargs`: Additional agent parameters

**Returns:**
- New RollbackAgent with restored state

## AgentService

High-level service for managing RollbackAgent instances.

### Class Definition

```python
class AgentService:
    def __init__(self, model_config: Optional[Dict[str, Any]] = None)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_config` | `Optional[Dict]` | `None` | Configuration for the AI model |

### Default Model Configuration

```python
{
    "id": "gpt-4o-mini",
    "temperature": 0.7
}
```

### Methods

#### create_new_agent(external_session_id: int, session_name: Optional[str] = None, **agent_kwargs) -> RollbackAgent

Create a new RollbackAgent for an external session.

```python
agent = service.create_new_agent(
    external_session_id=1,
    session_name="Python Tutorial"
)
```

**Parameters:**
- `external_session_id` (int): ID of external session
- `session_name` (Optional[str]): Name for the session
- `**agent_kwargs`: Additional agent arguments

**Returns:**
- New RollbackAgent instance

#### resume_agent(external_session_id: int, internal_session_id: Optional[int] = None) -> Optional[RollbackAgent]

Resume an existing agent session.

```python
agent = service.resume_agent(
    external_session_id=1,
    internal_session_id=5  # Optional, uses current if None
)
```

**Parameters:**
- `external_session_id` (int): ID of external session
- `internal_session_id` (Optional[int]): Specific internal session to resume

**Returns:**
- Resumed RollbackAgent or None if not found

#### rollback_to_checkpoint(external_session_id: int, checkpoint_id: int) -> Optional[RollbackAgent]

Create a new agent from a checkpoint.

```python
new_agent = service.rollback_to_checkpoint(
    external_session_id=1,
    checkpoint_id=5
)
```

**Parameters:**
- `external_session_id` (int): ID of external session
- `checkpoint_id` (int): ID of checkpoint to rollback to

**Returns:**
- New RollbackAgent with checkpoint state or None if failed

#### handle_agent_response(agent: RollbackAgent, response: Any) -> bool

Handle agent response and check for rollback requests.

```python
response = agent.run("Rollback to checkpoint 5")
if service.handle_agent_response(agent, response):
    checkpoint_id = agent.session_state.get('rollback_checkpoint_id')
    new_agent = service.rollback_to_checkpoint(
        external_session_id,
        checkpoint_id
    )
```

**Parameters:**
- `agent` (RollbackAgent): The agent that generated response
- `response`: The agent's response

**Returns:**
- `True` if rollback was requested, `False` otherwise

#### list_internal_sessions(external_session_id: int) -> list

List all internal sessions for an external session.

```python
sessions = service.list_internal_sessions(external_session_id=1)
for session in sessions:
    print(f"Session {session.id}: {session.checkpoint_count} checkpoints")
```

**Parameters:**
- `external_session_id` (int): ID of external session

**Returns:**
- List of InternalSession objects

#### list_checkpoints(internal_session_id: int) -> list

List all checkpoints for an internal session.

```python
checkpoints = service.list_checkpoints(internal_session_id=5)
for cp in checkpoints:
    print(f"Checkpoint {cp.id}: {cp.checkpoint_name}")
```

**Parameters:**
- `internal_session_id` (int): ID of internal session

**Returns:**
- List of Checkpoint objects

#### get_conversation_summary(agent: RollbackAgent) -> str

Get a summary of the conversation history.

```python
summary = service.get_conversation_summary(agent)
print(summary)
# Conversation (15 messages):
# [user] Hello, teach me Python
# [assistant] I'll help you learn Python...
# ... (last 10 messages shown)
```

**Parameters:**
- `agent` (RollbackAgent): The agent instance

**Returns:**
- Formatted conversation summary

## Usage Examples

### Basic Conversation with Checkpoints

```python
from src.agents.agent_service import AgentService

# Initialize service
service = AgentService()

# Create new agent
agent = service.create_new_agent(external_session_id=1)

# Have conversation
agent.run("Hello, I want to learn Python")
agent.run("What are variables?")

# Create checkpoint
agent.create_checkpoint("after-variables")

# Continue
agent.run("Now explain functions")

# Rollback if needed
agent.run("Actually, rollback to after-variables")
```

### Custom Tool Integration

```python
def calculate(expression: str) -> str:
    """Calculate mathematical expression."""
    return str(eval(expression))

# Create agent with custom tool
agent = RollbackAgent(
    external_session_id=1,
    model=model,
    tools=[calculate],
    auto_checkpoint=True  # Auto-checkpoint after calculate
)

agent.run("What's 5 * 10?")  # Auto-checkpoint created
```

### Advanced Session Management

```python
# Resume specific session
agent = service.resume_agent(
    external_session_id=1,
    internal_session_id=3
)

# Get session info
history = agent.get_conversation_history()
state = agent.get_session_state()
checkpoints = agent.list_checkpoints_tool()

# Rollback to specific checkpoint
new_agent = service.rollback_to_checkpoint(
    external_session_id=1,
    checkpoint_id=5
)
```

## Error Handling

```python
try:
    agent = service.create_new_agent(external_session_id=1)
    response = agent.run("Hello")
except ValueError as e:
    print(f"Invalid session: {e}")
except Exception as e:
    print(f"Error: {e}")

# Handle rollback failures
new_agent = service.rollback_to_checkpoint(1, 999)
if new_agent is None:
    print("Checkpoint not found")
```

## Best Practices

1. **Always name important checkpoints**
   ```python
   agent.create_checkpoint("working-solution-v1")
   ```

2. **Clean up automatic checkpoints periodically**
   ```python
   agent.cleanup_auto_checkpoints_tool(keep_latest=5)
   ```

3. **Check rollback requests after each run**
   ```python
   response = agent.run(user_input)
   if service.handle_agent_response(agent, response):
       # Perform rollback
   ```

4. **Use repositories for direct database access**
   ```python
   from src.database.repositories.checkpoint_repository import CheckpointRepository
   repo = CheckpointRepository()
   all_checkpoints = repo.find_all()
   ```