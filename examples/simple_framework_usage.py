"""Simple example using the rollback agent framework."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.rollback_agent.app import RollbackAgentApp


def main():
    """Run the rollback agent application."""
    app = RollbackAgentApp(db_file="data/rollback_agent.db")
    app.run()


if __name__ == "__main__":
    main()

