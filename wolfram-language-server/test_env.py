#!/usr/bin/env python3
"""Test environment variable loading."""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
print(f"Loading .env from: {env_path}")
print(f".env file exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)

# Test environment variables
print("\nEnvironment Variables:")
print(f"WOLFRAM_KERNEL_PATH: {os.getenv('WOLFRAM_KERNEL_PATH')}")
print(f"API_KEY: {os.getenv('API_KEY')}")
print(f"HOST: {os.getenv('HOST')}")
print(f"PORT: {os.getenv('PORT')}")
print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL')}")

# Test that it works in main module
print("\nTesting main module import...")
try:
    from wolfram_language_server.main import logger
    print("✅ Main module imported successfully")
    print(f"Logger level: {logger.level}")
except Exception as e:
    print(f"❌ Error importing main module: {e}")