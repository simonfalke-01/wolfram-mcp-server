#!/usr/bin/env python3
"""Simple runner script for the Wolfram Language Server."""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    uvicorn.run(
        "wolfram_language_server.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )