#!/usr/bin/env python3
"""Example CLI usage of the Rollback Agent System.

This demonstrates the full workflow:
1. User authentication (login/register)
2. Session management (create/resume)
3. Agent interaction with checkpoint management
4. Admin features for rootusr
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ui.cli import main


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          Rollback Agent System - CLI Demo               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  This demo showcases:                                   ║
    ║  • User authentication (login/register)                 ║
    ║  • Session management (external sessions)               ║
    ║  • Agent interaction with checkpoints                   ║
    ║  • Admin features (user management)                     ║
    ║                                                          ║
    ║  Default admin credentials:                             ║
    ║  Username: rootusr                                      ║
    ║  Password: 1234                                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run the CLI
    main()