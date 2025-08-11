"""Database utilities for rollback agent."""
import sqlite3
from pathlib import Path
from typing import Optional


def init_database(db_file: str = "data/rollback_agent.db"):
    """Initialize database with required tables."""
    Path(db_file).parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Create rollback_sessions table if it doesn't exist
    # This mimics what Agno's SqliteStorage creates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rollback_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            memory TEXT,
            session_data TEXT,
            extra_data TEXT,
            created_at TEXT,
            updated_at TEXT,
            agent_id TEXT,
            agent_data TEXT,
            team_session_id TEXT
        )
    """)

    # Create rollback_states table for future use
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rollback_states (
            rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_session_id TEXT NOT NULL,
            new_session_id TEXT,
            checkpoint_data TEXT NOT NULL,
            rollback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # Add user_id column to rollback_sessions if it doesn't exist
    # First check if column exists
    cursor.execute("PRAGMA table_info(rollback_sessions)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'user_id' not in columns:
        cursor.execute("""
            ALTER TABLE rollback_sessions 
            ADD COLUMN user_id INTEGER
        """)

    if 'session_name' not in columns:
        cursor.execute("""
            ALTER TABLE rollback_sessions 
            ADD COLUMN session_name TEXT
        """)

    if 'last_activity' not in columns:
        cursor.execute("""
            ALTER TABLE rollback_sessions 
            ADD COLUMN last_activity TIMESTAMP
        """)
        # Update existing rows to have current timestamp
        cursor.execute("""
          UPDATE rollback_sessions 
          SET last_activity = CURRENT_TIMESTAMP 
          WHERE last_activity IS NULL
      """)

    if 'is_active' not in columns:
        cursor.execute("""
            ALTER TABLE rollback_sessions 
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE
        """)

    if 'parent_session_id' not in columns:
        cursor.execute("""
            ALTER TABLE rollback_sessions 
            ADD COLUMN parent_session_id TEXT
        """)

    conn.commit()
    conn.close()


def get_db_connection(db_file: str = "data/rollback_agent.db") -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn
