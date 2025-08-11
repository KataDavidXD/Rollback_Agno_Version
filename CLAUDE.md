# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Rollback Agent** framework built on top of the Agno library, providing checkpoint and rollback capabilities for AI conversations. The agent can create checkpoints during conversations and roll back to previous states, making it useful for experimentation and conversation management.

## Key Architecture Components

### Core Agent (`src/rollback_agent/agent.py`)
- `create_rollback_agent()` - Factory function that creates configured Agent instances
- Uses OpenAI GPT models via Agno framework
- Implements SQLite storage for persistence
- Configurable auto-checkpoint intervals and checkpoint limits

### Checkpoint System (`src/rollback_agent/tools/checkpoint.py`)
- **Four main tools**: `create_checkpoint`, `list_checkpoints`, `delete_checkpoint`, `rollback_to_checkpoint`
- Checkpoints store conversation snapshots, session state, and metadata
- Rollback creates new sessions with restored conversation history
- Automatic checkpoint pruning based on `max_checkpoints` setting

### Session Management
- **SessionManager** (`managers/session_manager.py`) - Handles agent session lifecycle
- **ConversationManager** (`managers/conversation_manager.py`) - Manages interactive conversations
- **RollbackManager** (`managers/rollback_manager.py`) - Handles rollback state restoration

### Authentication & Multi-user Support
- **UserManager** (`auth/user_manager.py`) - User registration, login, session tracking
- SQLite database for user data and session persistence
- Password hashing for security

## Data Models
- **Checkpoint** (`models/checkpoint.py`) - Stores conversation snapshots and metadata
- **User** (`models/user.py`) - User authentication and session data
- Database initialization handled by `utils/database.py`

## Running the Application

### Basic Usage (Simple Interactive)
```bash
python examples/basic_usage.py
```

### Full Application (With Authentication)
```bash
python examples/usage_with_auth.py
```

### Framework Integration
```bash
python examples/simple_framework_usage.py
```

## Dependencies
- **agno>=0.1.0** - Core AI agent framework
- **openai** - OpenAI API integration  
- **sqlalchemy** - Database ORM
- **packaging** - Utility library

## Development Notes

The rollback mechanism works by:
1. Creating conversation snapshots at checkpoint time
2. When rolling back, clearing current session and creating new session with restored state
3. Conversation history gets restored as context in the new session
4. Session state (including remaining checkpoints) is preserved across rollback

Database file defaults to `data/rollback_agent.db` and is created automatically on first run.