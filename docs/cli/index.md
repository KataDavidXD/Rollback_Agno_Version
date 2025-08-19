# CLI Guide

## Overview

The Rollback Agent System includes a comprehensive Command-Line Interface (CLI) that provides full access to all system features through an interactive terminal interface.

## Starting the CLI

```bash
# Basic startup
python example/advanced_cli.py

# With environment variable
export OPENAI_API_KEY='your-key-here'
python example/advanced_cli.py

# With custom database path
DATABASE_PATH=/custom/path python example/advanced_cli.py
```

## CLI Structure

```
┌─────────────────────────┐
│   Authentication Menu   │
│   ├── Login            │
│   └── Register         │
└─────────┬───────────────┘
          │
┌─────────▼───────────────┐
│      Main Menu          │
│   ├── Session Mgmt     │
│   ├── User Profile     │
│   └── Admin Panel      │
└─────────┬───────────────┘
          │
┌─────────▼───────────────┐
│    Chat Interface       │
│   with Commands         │
└─────────────────────────┘
```

## Authentication

### First Time Setup

```
============================================================
              ROLLBACK AGENT SYSTEM
============================================================

1. Login
2. Register
0. Exit

▶ Enter choice: 2

============================================================
                    REGISTER
============================================================

▶ Choose username: alice
▶ Choose password: ********
▶ Confirm password: ********

✓ Registration successful! Welcome, alice!
```

### Login

```
▶ Enter choice: 1

============================================================
                      LOGIN
============================================================

▶ Username: alice
▶ Password: ********

✓ Welcome back, alice!
```

## Main Menu

After authentication, you'll see the main menu:

```
============================================================
                    MAIN MENU
============================================================
Logged in as: alice

1. Session Management
2. User Profile
3. Admin Panel (admin only)
0. Logout

▶ Enter choice:
```

## Session Management

### Creating a New Session

```
▶ Enter choice: 1

============================================================
              SESSION MANAGEMENT
============================================================
You have 0 session(s)

1. Create New Session
2. List My Sessions
3. Resume Session
4. Delete Session
0. Back to Main Menu

▶ Enter choice: 1

============================================================
              CREATE NEW SESSION
============================================================

▶ Session name (or press Enter for default): Python Learning
✓ Created session: Python Learning

▶ Start chatting now? (y/n): y
```

### Listing Sessions

The CLI displays sessions in a hierarchical structure:

```
============================================================
                  MY SESSIONS
============================================================

📁 Python Learning
   ID: 1 | Created: 2024-01-15 10:30
   Internal Sessions:
     ✓ Current ID: 1 | Created: 01-15 10:30 | Checkpoints: 5
       ID: 2 | Created: 01-15 11:00 | Checkpoints: 3

📁 Machine Learning Project
   ID: 2 | Created: 2024-01-14 09:00
   Internal Sessions:
       ID: 3 | Created: 01-14 09:00 | Checkpoints: 10
```

### Resuming a Session

```
▶ Enter choice: 3

============================================================
                RESUME SESSION
============================================================
Available sessions:

1. Python Learning (Created: 2024-01-15 10:30)
2. Machine Learning Project (Created: 2024-01-14 09:00)

0. Cancel

▶ Select session: 1

============================================================
        SESSION: Python Learning
============================================================
Internal sessions:

1. [✓] Session 1 (Created: 2024-01-15 10:30, Checkpoints: 5)
2. [ ] Session 2 (Created: 2024-01-15 11:00, Checkpoints: 3)

3. Create new internal session
0. Cancel

▶ Select internal session: 1

ℹ Resuming session 1...
✓ Session resumed successfully!

Recent conversation:
[USER] What are Python decorators?
[ASSISTANT] Python decorators are a powerful feature that...
```

## Chat Interface

### Basic Chat

Once in a chat session, you can have natural conversations:

```
============================================================
           CHAT: Python Learning
============================================================
Commands:
  /checkpoints - List checkpoints
  /checkpoint <name> - Create checkpoint
  /rollback <id/name> - Rollback to checkpoint
  /history - Show conversation history
  /clear - Clear screen
  /exit - Exit chat

Type your message or command:

You: Hello, I want to learn about Python functions
Agent: I'd be happy to help you learn about Python functions! Functions are...

You: Can you show me an example?
Agent: Certainly! Here's a simple example of a Python function...
```

### Chat Commands

#### /checkpoints

Lists all available checkpoints:

```
You: /checkpoints

Checkpoints:
  [MANUAL] ID: 1 | Initial state | Created: 10:30:15
  [AUTO] ID: 2 | After calculate_tool | Created: 10:35:20
  [MANUAL] ID: 3 | Before advanced topics | Created: 10:40:00
  [AUTO] ID: 4 | After weather_tool | Created: 10:45:30
```

#### /checkpoint <name>

Creates a manual checkpoint:

```
You: /checkpoint before-decorators
✓ Checkpoint 'before-decorators' created successfully (ID: 5)
```

#### /rollback <id/name>

Rollback to a specific checkpoint:

```
You: /rollback before-decorators

⚠ Rolling back to checkpoint 5 (before-decorators)...
✓ Rollback completed successfully!

Restored to this point in conversation:
[USER] What are functions in Python?
[ASSISTANT] Functions in Python are reusable blocks of code...
```

#### /history

Shows complete conversation history:

```
You: /history

Conversation History:

[USER]
Hello, I want to learn Python

[ASSISTANT]
I'd be happy to help you learn Python! Python is a versatile...

[USER]
What are variables?

[ASSISTANT]
Variables in Python are containers for storing data values...
```

#### /clear

Clears the screen and shows header:

```
You: /clear

============================================================
           CHAT: Python Learning
============================================================
```

#### /exit

Exits the chat interface:

```
You: /exit

▶ Exit chat? (y/n): y
```

## User Profile

Access your profile settings:

```
============================================================
                USER PROFILE
============================================================
Username: alice
User ID: 1
Admin: No
Member since: 2024-01-15
Total sessions: 3

1. Change Password
0. Back

▶ Enter choice: 1

========================================
Current password: ********
New password: ********
Confirm new password: ********

✓ Password changed successfully
```

## Admin Panel

Available only for admin users:

```
============================================================
                ADMIN PANEL
============================================================

1. List All Users
2. Delete User
3. System Statistics
0. Back

▶ Enter choice: 3

============================================================
            SYSTEM STATISTICS
============================================================
Users:
  Total: 10
  Admins: 2
  Regular: 8

Sessions:
  External Sessions: 25
  Internal Sessions: 47
  Total Checkpoints: 234
  Avg Internal/External: 1.9
  Avg Checkpoints/Session: 5.0
```

### Admin User Management

```
▶ Enter choice: 1

============================================================
                ALL USERS
============================================================
Total users: 10

• alice
  ID: 1 | Created: 2024-01-15 | Sessions: 3
• bob [ADMIN]
  ID: 2 | Created: 2024-01-14 | Sessions: 5
• charlie
  ID: 3 | Created: 2024-01-16 | Sessions: 1
```

## Color Coding

The CLI uses colors for better readability:

- **Blue** (Cyan): Information messages, commands
- **Green**: Success messages, assistant responses
- **Yellow**: Warnings, important notices
- **Red**: Errors, failures
- **Bold**: Important text, headers
- **Regular**: Normal text

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Interrupt current operation |
| `Ctrl+D` | Exit (on empty line) |
| `Enter` | Submit input |
| `Arrow keys` | Navigate history (in shell) |

## Error Messages

Common error messages and their meanings:

### Authentication Errors

```
✗ Login failed: Invalid credentials
```
**Solution**: Check username and password

```
✗ Registration failed: Username already exists
```
**Solution**: Choose a different username

### Session Errors

```
✗ Failed to create session
```
**Solution**: Check database permissions

```
✗ Checkpoint 'xyz' not found
```
**Solution**: Use `/checkpoints` to see available checkpoints

### System Errors

```
Error: OPENAI_API_KEY environment variable not set
```
**Solution**: Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-key-here'
```

## Tips and Tricks

### 1. Quick Session Creation

Start chatting immediately after creating a session:

```
▶ Session name: Quick Test
▶ Start chatting now? (y/n): y
# Goes directly to chat interface
```

### 2. Checkpoint Naming Convention

Use descriptive names for checkpoints:

```
/checkpoint before-complex-code
/checkpoint working-solution-v1
/checkpoint after-refactoring
```

### 3. Efficient Navigation

Use numbers for quick menu navigation:

```
# Instead of typing full commands
▶ Enter choice: 1  # Faster than typing "Session Management"
```

### 4. Batch Operations

Clean up checkpoints periodically:

```
You: Let's clean up old auto-checkpoints, keep only the latest 3
Agent: ✓ Cleaned up 12 old automatic checkpoints. Kept the latest 3.
```

### 5. Session Organization

Name sessions by project or topic:

```
- "Python Tutorial - Basics"
- "Python Tutorial - Advanced"
- "Web Development - Frontend"
- "Web Development - Backend"
```

## Command Reference

### Authentication Commands

| Menu Option | Description |
|-------------|-------------|
| Login | Authenticate existing user |
| Register | Create new account |
| Exit | Close application |

### Main Menu Commands

| Menu Option | Description |
|-------------|-------------|
| Session Management | Manage conversation sessions |
| User Profile | View/edit profile settings |
| Admin Panel | Admin-only functions |
| Logout | Sign out current user |

### Session Commands

| Menu Option | Description |
|-------------|-------------|
| Create New Session | Start new conversation project |
| List My Sessions | View all your sessions |
| Resume Session | Continue existing conversation |
| Delete Session | Remove session and data |

### Chat Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/checkpoints` | List all checkpoints | `/checkpoints` |
| `/checkpoint <name>` | Create checkpoint | `/checkpoint v1` |
| `/rollback <id/name>` | Rollback to checkpoint | `/rollback 5` |
| `/history` | Show conversation | `/history` |
| `/clear` | Clear screen | `/clear` |
| `/exit` | Leave chat | `/exit` |

## Troubleshooting

### CLI Won't Start

```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check API key
echo $OPENAI_API_KEY
```

### Colors Not Working

```bash
# Check terminal support
echo $TERM  # Should show color-capable terminal

# Disable colors if needed
NO_COLOR=1 python example/advanced_cli.py
```

### Session Issues

```python
# Reset database (WARNING: deletes all data)
rm data/rollback.db
python example/advanced_cli.py  # Will create fresh database
```

## Advanced Usage

### Custom CLI Extensions

You can extend the CLI with custom commands:

```python
# In advanced_cli.py
def handle_custom_command(self, command: str) -> bool:
    """Add custom commands."""
    if command == "/stats":
        # Show statistics
        self.show_statistics()
    elif command.startswith("/export"):
        # Export conversation
        self.export_conversation()
    # ... more custom commands
```

### Scripting

Automate CLI interactions:

```bash
# Create expect script for automation
#!/usr/bin/expect
spawn python example/advanced_cli.py
expect "Enter choice:"
send "1\r"
expect "Username:"
send "alice\r"
expect "Password:"
send "password123\r"
# ... continue automation
```

## Next Steps

- [API Reference](../api/index.md) - Program against the API
- [Examples](../examples/index.md) - Code examples
- [Architecture](../architecture/overview.md) - System internals