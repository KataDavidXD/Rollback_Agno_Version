# Installation

## Prerequisites

Before installing the Rollback Agent System, ensure you have:

- **Python 3.8+** installed on your system
- **pip** package manager
- **OpenAI API Key** for the AI model
- **Git** (optional, for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/rollback-agent.git
cd rollback-agent
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

#### OpenAI API Key

```bash
# On macOS/Linux:
export OPENAI_API_KEY='your-api-key-here'

# On Windows:
set OPENAI_API_KEY=your-api-key-here

# Or create a .env file:
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 5. Verify Installation

```bash
# Run the test script
python -c "from src.agents.rollback_agent import RollbackAgent; print('✓ Installation successful!')"
```

## Quick Test

Run a simple test to ensure everything is working:

```bash
# Test the basic functionality
python tests/test_basic_agent.py

# Run the advanced CLI
python example/advanced_cli.py
```

## Dependencies

The main dependencies include:

- **agno** - Core AI agent framework
- **openai** - OpenAI API client
- **sqlalchemy** - Database ORM
- **python-dotenv** - Environment variable management
- **rich** - Terminal formatting (optional)

## Directory Structure

After installation, your directory should look like:

```
rollback-agent/
├── src/               # Source code
├── tests/             # Test files
├── example/           # Example scripts
├── data/              # Data storage (created automatically)
│   ├── rollback.db    # Main database
│   └── agno_sessions.db # Agno session storage
├── docs/              # Documentation
└── requirements.txt   # Python dependencies
```

## Configuration

### Database Location

By default, databases are stored in the `data/` directory. You can change this by modifying:

```python
# In your code
DATABASE_PATH = "custom/path/to/database.db"
```

### Model Configuration

Default model is `gpt-4o-mini`. To change:

```python
model_config = {
    "id": "gpt-4",  # or "gpt-3.5-turbo"
    "temperature": 0.7
}
```

## Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'agno'

```bash
pip install agno
```

#### 2. OpenAI API Key Not Found

Ensure your API key is set:

```bash
echo $OPENAI_API_KEY  # Should display your key
```

#### 3. Database Permission Error

Ensure the `data/` directory has write permissions:

```bash
chmod 755 data/
```

#### 4. Python Version Error

Check your Python version:

```bash
python --version  # Should be 3.8 or higher
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Start using the system
- [Architecture Overview](../architecture/overview.md) - Understand the system design
- [API Reference](../api/index.md) - Detailed API documentation