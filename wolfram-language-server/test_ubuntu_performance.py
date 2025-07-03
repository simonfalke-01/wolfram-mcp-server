#!/usr/bin/env python3
"""Test script to compare Wolfram Engine performance on Ubuntu vs macOS."""

import asyncio
import time
import sys
import os

# Add the source directory to path
sys.path.insert(0, "wolfram-language-server/src")

from wolfram_language_server.wolfram_client import WolframLanguageClient
from wolfram_language_server.wolfram_client_improved import ImprovedWolframLanguageClient


async def test_basic_performance():
    """Test basic Wolfram performance."""
    print("=== Basic Wolfram Engine Performance Test ===")
    
    # Test simple calculations
    test_cases = [
        "2 + 2",
        "Solve[x^2 + 2x - 3 == 0, x]",
        "Integrate[x^2, x]",
        "Prime[100]"
    ]
    
    for i, code in enumerate(test_cases, 1):
        print(f"\nTest {i}: {code}")
        
        # Test current client
        print("  Current client:")
        client = WolframLanguageClient()
        
        start_time = time.time()
        success, result, error, exec_time = await client.execute_wolfram_code(code, timeout=60)
        total_time = time.time() - start_time
        
        if success:
            print(f"    ✓ Result: {result}")
            print(f"    ✓ Execution time: {exec_time:.3f}s")
            print(f"    ✓ Total time: {total_time:.3f}s")
        else:
            print(f"    ✗ Error: {error}")
            print(f"    ✗ Total time: {total_time:.3f}s")
        
        await client.close()
        
        # Test improved client
        print("  Improved client:")
        improved_client = ImprovedWolframLanguageClient()
        
        start_time = time.time()
        success, result, error, exec_time = await improved_client.execute_wolfram_code(code, timeout=60)
        total_time = time.time() - start_time
        
        if success:
            print(f"    ✓ Result: {result}")
            print(f"    ✓ Execution time: {exec_time:.3f}s")
            print(f"    ✓ Total time: {total_time:.3f}s")
        else:
            print(f"    ✗ Error: {error}")
            print(f"    ✗ Total time: {total_time:.3f}s")
        
        await improved_client.close()


async def test_session_reuse():
    """Test session reuse performance."""
    print("\n=== Session Reuse Performance Test ===")
    
    # Test multiple operations with the same client (should reuse session)
    operations = ["2 + 2", "3 + 3", "4 + 4", "5 + 5"]
    
    print("\nTesting improved client with session reuse:")
    client = ImprovedWolframLanguageClient()
    
    total_start = time.time()
    
    for i, code in enumerate(operations, 1):
        start_time = time.time()
        success, result, error, exec_time = await client.execute_wolfram_code(code, timeout=30)
        total_time = time.time() - start_time
        
        print(f"  Operation {i}: {code}")
        if success:
            print(f"    ✓ Result: {result} (exec: {exec_time:.3f}s, total: {total_time:.3f}s)")
        else:
            print(f"    ✗ Error: {error} (total: {total_time:.3f}s)")
    
    total_duration = time.time() - total_start
    print(f"\nTotal time for all operations: {total_duration:.3f}s")
    print(f"Average time per operation: {total_duration/len(operations):.3f}s")
    
    # Get session info
    session_info = await client.get_session_info()
    print(f"\nSession info: {session_info}")
    
    await client.close()


async def test_environment_info():
    """Test environment and system information."""
    print("\n=== Environment Information ===")
    
    # System info
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    # Try to get Wolfram info
    client = ImprovedWolframLanguageClient()
    
    try:
        # Get detailed Wolfram information
        tests = [
            ("$Version", "Wolfram version"),
            ("$SystemID", "System ID"),
            ("$ProcessorType", "Processor type"),
            ("$OperatingSystem", "Operating system"),
            ("$MemoryAvailable", "Memory available"),
            ("$LicenseID", "License ID"),
            ("$KernelID", "Kernel ID")
        ]
        
        for code, description in tests:
            try:
                success, result, error, exec_time = await client.execute_wolfram_code(code, timeout=10)
                if success:
                    print(f"{description}: {result} ({exec_time:.3f}s)")
                else:
                    print(f"{description}: ERROR - {error}")
            except Exception as e:
                print(f"{description}: EXCEPTION - {e}")
    
    finally:
        await client.close()


async def main():
    """Run all performance tests."""
    print("Wolfram Engine Performance Diagnostic Tool")
    print("=" * 50)
    
    try:
        await test_environment_info()
        await test_basic_performance()
        await test_session_reuse()
        
        print("\n" + "=" * 50)
        print("DIAGNOSIS GUIDE:")
        print("- If the first operation takes >10s, kernel startup is slow")
        print("- If subsequent operations are still slow, there's a configuration issue")
        print("- If 'improved client' is faster, session reuse is the solution")
        print("- Compare timing between Ubuntu and macOS versions")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())