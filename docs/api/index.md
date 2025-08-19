# API Reference

## Overview

The Rollback Agent System provides a comprehensive API for managing AI conversations with checkpoint and rollback capabilities. This reference covers all public APIs and their usage.

## Core Components

### [RollbackAgent](agents.md)
The main agent class with checkpoint and rollback capabilities.

```python
from src.agents.rollback_agent import RollbackAgent

agent = RollbackAgent(
    external_session_id=1,
    model=model,
    auto_checkpoint=True
)
```

### [AgentService](agents.md#agentservice)
High-level service for managing agents.

```python
from src.agents.agent_service import AgentService

service = AgentService()
agent = service.create_new_agent(external_session_id=1)
```

### [Authentication](auth/user.md)
User authentication and management.

```python
from src.auth.auth_service import AuthService

auth = AuthService()
success, user, message = auth.login(username, password)
```

### [Sessions](sessions.md)
Session hierarchy management.

```python
from src.sessions.external_session import ExternalSession
from src.sessions.internal_session import InternalSession

session = ExternalSession(user_id=1, session_name="My Project")
```

### [Checkpoints](checkpoints.md)
Checkpoint creation and management.

```python
from src.checkpoints.checkpoint import Checkpoint

checkpoint = Checkpoint.from_internal_session(
    internal_session,
    checkpoint_name="Important State"
)
```

### [Repositories](database/repositories.md)
Data access layer using repository pattern.

```python
from src.database.repositories.checkpoint_repository import CheckpointRepository

repo = CheckpointRepository()
checkpoint = repo.get_by_id(checkpoint_id)
```

## Quick Reference

### Agent Operations

| Method | Description | Example |
|--------|-------------|---------|
| `agent.run(message)` | Process user message | `agent.run("Hello")` |
| `agent.create_checkpoint(name)` | Create manual checkpoint | `agent.create_checkpoint("v1")` |
| `agent.list_checkpoints_tool()` | List all checkpoints | `checkpoints = agent.list_checkpoints_tool()` |
| `agent.rollback_to_checkpoint_tool(id)` | Request rollback | `agent.rollback_to_checkpoint_tool(5)` |
| `agent.get_conversation_history()` | Get chat history | `history = agent.get_conversation_history()` |

### Service Operations

| Method | Description | Example |
|--------|-------------|---------|
| `service.create_new_agent()` | Create new agent | `agent = service.create_new_agent(session_id)` |
| `service.resume_agent()` | Resume existing agent | `agent = service.resume_agent(session_id)` |
| `service.rollback_to_checkpoint()` | Perform rollback | `new_agent = service.rollback_to_checkpoint(session_id, checkpoint_id)` |
| `service.list_internal_sessions()` | List sessions | `sessions = service.list_internal_sessions(external_id)` |

### Authentication Operations

| Method | Description | Example |
|--------|-------------|---------|
| `auth.register()` | Register new user | `success, user, msg = auth.register(username, password)` |
| `auth.login()` | Authenticate user | `success, user, msg = auth.login(username, password)` |
| `auth.change_password()` | Update password | `success, msg = auth.change_password(username, old, new)` |
| `auth.delete_user()` | Remove user | `success, msg = auth.delete_user(username, admin_user)` |

### Repository Operations

| Method | Description | Example |
|--------|-------------|---------|
| `repo.create(entity)` | Create new entity | `saved = repo.create(checkpoint)` |
| `repo.get_by_id(id)` | Retrieve by ID | `entity = repo.get_by_id(1)` |
| `repo.update(entity)` | Update entity | `success = repo.update(entity)` |
| `repo.delete(id)` | Delete entity | `success = repo.delete(1)` |
| `repo.find_all()` | Get all entities | `all_items = repo.find_all()` |

## Error Handling

### Common Exceptions

```python
try:
    agent = service.rollback_to_checkpoint(session_id, checkpoint_id)
except ValueError as e:
    print(f"Rollback failed: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
```

### Error Responses

```python
# Authentication errors
success, user, message = auth.login(username, password)
if not success:
    print(f"Login failed: {message}")
    # message could be: "Invalid credentials", "User not found", etc.

# Rollback errors
agent = service.rollback_to_checkpoint(session_id, checkpoint_id)
if agent is None:
    print("Rollback failed - checkpoint not found")
```

## Type Definitions

### Response Types

```python
from typing import Optional, Dict, Any, List, Tuple

# Agent response
Response = Union[str, Dict[str, Any]]

# Authentication response
AuthResponse = Tuple[bool, Optional[User], str]

# Repository response
EntityResponse = Optional[Entity]
```

### Entity Types

```python
# User entity
class User:
    id: int
    username: str
    password_hash: str
    is_admin: bool
    created_at: datetime
    metadata: Dict[str, Any]

# Session entity
class ExternalSession:
    id: int
    user_id: int
    session_name: str
    created_at: datetime
    metadata: Dict[str, Any]

# Checkpoint entity
class Checkpoint:
    id: int
    internal_session_id: int
    checkpoint_name: str
    session_state: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    is_auto: bool
    created_at: datetime
    metadata: Dict[str, Any]
```

## Configuration

### Model Configuration

```python
model_config = {
    "id": "gpt-4o-mini",  # Model ID
    "temperature": 0.7,    # Creativity level
    "max_tokens": 2000,    # Max response length
    "top_p": 0.9          # Nucleus sampling
}

service = AgentService(model_config=model_config)
```

### Agent Configuration

```python
agent = RollbackAgent(
    external_session_id=1,
    model=model,
    auto_checkpoint=True,           # Auto-checkpoint after tools
    add_history_to_messages=True,   # Include conversation context
    num_history_runs=5,             # Messages to include
    show_tool_calls=True,           # Display tool usage
    tools=[custom_tool],            # Custom tools
    tool_hooks=[logging_hook]       # Tool call hooks
)
```

### Database Configuration

```python
# Custom database path
DATABASE_PATH = "custom/path/to/database.db"

# Repository with custom path
repo = CheckpointRepository(db_path=DATABASE_PATH)
```

## Async Support

The system currently uses synchronous operations. For async support:

```python
# Future async support (planned)
async def async_run():
    response = await agent.async_run("Hello")
    return response
```

## Pagination

For large result sets:

```python
# Get paginated results
checkpoints = repo.get_by_internal_session(
    session_id,
    limit=10,
    offset=20
)

# Get total count
total = repo.count_by_internal_session(session_id)
```

## Filtering and Sorting

```python
# Filter checkpoints
manual_checkpoints = repo.get_by_internal_session(
    session_id,
    auto_only=False
)

# Sort by creation date
checkpoints = sorted(
    checkpoints,
    key=lambda x: x.created_at,
    reverse=True
)
```

## Webhooks and Events

```python
# Tool hook example
def on_tool_call(function_name: str, function_call, arguments: Dict[str, Any]):
    print(f"Tool called: {function_name}")
    result = function_call(**arguments)
    print(f"Tool result: {result}")
    return result

agent = RollbackAgent(
    external_session_id=1,
    model=model,
    tool_hooks=[on_tool_call]
)
```

## Rate Limiting

Best practices for API usage:

```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_second=2)
def call_agent(message):
    return agent.run(message)
```

## Testing

```python
import unittest
from unittest.mock import Mock, patch

class TestRollbackAgent(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.agent = RollbackAgent(
            external_session_id=1,
            model=self.model
        )
    
    def test_checkpoint_creation(self):
        checkpoint = self.agent.create_checkpoint("test")
        self.assertIn("created successfully", checkpoint)
    
    def test_conversation_history(self):
        self.agent.run("Hello")
        history = self.agent.get_conversation_history()
        self.assertEqual(len(history), 2)  # User + Assistant
```

## Next Steps

- [RollbackAgent API](agents.md) - Detailed agent documentation
- [Authentication API](auth/user.md) - User management
- [Repository API](database/repositories.md) - Data access layer
- [Session API](sessions.md) - Session management
- [Checkpoint API](checkpoints.md) - Checkpoint operations