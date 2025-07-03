#!/usr/bin/env python3
"""Simple test script for the Wolfram Language Server."""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wolfram_language_server.models import HealthResponse
from wolfram_language_server.wolfram_client import WolframExecutor


async def test_wolfram_client():
    """Test the Wolfram client."""
    print("Testing Wolfram client...")
    
    executor = WolframExecutor()
    
    # Test availability
    available, error = await executor.is_available()
    print(f"Wolfram available: {available}")
    if error:
        print(f"Error: {error}")
    
    # Test kernel info
    info = await executor.get_kernel_info()
    print(f"Kernel info: {info}")
    
    await executor.stop_session()


async def test_simple_execution():
    """Test simple code execution."""
    print("\nTesting simple execution...")
    
    try:
        executor = WolframExecutor()
        success, result, error, time_taken = await executor.execute_code("1 + 1", timeout=5)
        print(f"Success: {success}")
        print(f"Result: {result}")
        print(f"Error: {error}")
        print(f"Time: {time_taken}")
        await executor.stop_session()
    except Exception as e:
        print(f"Exception: {e}")


def test_models():
    """Test Pydantic models."""
    print("\nTesting models...")
    
    health = HealthResponse(
        status="healthy",
        version="0.1.0",
        wolfram_available=False,
        kernel_info=None
    )
    print(f"Health model: {health.model_dump()}")


async def main():
    """Run all tests."""
    print("=== Wolfram Language Server Tests ===\n")
    
    test_models()
    await test_wolfram_client()
    await test_simple_execution()
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())