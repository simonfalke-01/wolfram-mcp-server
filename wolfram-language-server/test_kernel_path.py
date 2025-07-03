#!/usr/bin/env python3
"""Test Wolfram kernel path loading."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from wolfram_language_server.wolfram_client import WolframExecutor

async def test_kernel_path():
    """Test that kernel path is being used."""
    kernel_path = os.getenv("WOLFRAM_KERNEL_PATH")
    print(f"Kernel path from env: {kernel_path}")
    
    executor = WolframExecutor(kernel_path=kernel_path)
    print(f"Executor kernel path: {executor.kernel_path}")
    
    # Test availability
    available, error = await executor.is_available()
    print(f"Wolfram available: {available}")
    if error:
        print(f"Error: {error}")
    
    await executor.stop_session()

if __name__ == "__main__":
    asyncio.run(test_kernel_path())