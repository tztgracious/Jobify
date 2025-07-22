"""
Jobify Backend Django Project

This module initializes the project-wide logger and ensures the logs directory exists.
"""

import os
from pathlib import Path

# Ensure logs directory exists
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)