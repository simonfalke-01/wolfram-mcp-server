#!/usr/bin/env python3
"""Debug script to test Wolfram Engine performance directly."""

import time
import sys
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wlexpr

def test_wolfram_performance():
    """Test Wolfram Engine performance step by step."""
    
    print("=== Wolfram Engine Performance Test ===")
    print(f"Python version: {sys.version}")
    
    # Test 1: Session creation time
    print("\n1. Testing session creation...")
    start_time = time.time()
    
    try:
        session = WolframLanguageSession()
        creation_time = time.time() - start_time
        print(f"   ✓ Session created in {creation_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Session creation failed: {e}")
        return
    
    # Test 2: First evaluation (includes kernel startup)
    print("\n2. Testing first evaluation (includes kernel startup)...")
    start_time = time.time()
    
    try:
        result = session.evaluate(wlexpr("2 + 2"))
        first_eval_time = time.time() - start_time
        print(f"   ✓ First evaluation: {result} in {first_eval_time:.3f}s")
    except Exception as e:
        print(f"   ✗ First evaluation failed: {e}")
        session.terminate()
        return
    
    # Test 3: Second evaluation (should be faster)
    print("\n3. Testing second evaluation (should be faster)...")
    start_time = time.time()
    
    try:
        result = session.evaluate(wlexpr("3 + 3"))
        second_eval_time = time.time() - start_time
        print(f"   ✓ Second evaluation: {result} in {second_eval_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Second evaluation failed: {e}")
    
    # Test 4: Complex calculation
    print("\n4. Testing complex calculation...")
    start_time = time.time()
    
    try:
        result = session.evaluate(wlexpr("Solve[x^2 + 2x - 3 == 0, x]"))
        complex_eval_time = time.time() - start_time
        print(f"   ✓ Complex evaluation: {result} in {complex_eval_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Complex evaluation failed: {e}")
    
    # Test 5: Check kernel info
    print("\n5. Testing kernel info...")
    try:
        kernel_info = session.evaluate(wlexpr("$Version"))
        print(f"   ✓ Kernel version: {kernel_info}")
        
        memory_info = session.evaluate(wlexpr("MemoryInUse[]"))
        print(f"   ✓ Memory in use: {memory_info}")
        
        license_info = session.evaluate(wlexpr("$LicenseID"))
        print(f"   ✓ License ID: {license_info}")
    except Exception as e:
        print(f"   ✗ Kernel info failed: {e}")
    
    # Clean up
    print("\n6. Cleaning up...")
    try:
        session.terminate()
        print("   ✓ Session terminated")
    except Exception as e:
        print(f"   ✗ Session termination failed: {e}")
    
    print("\n=== Test Complete ===")
    print("If the first evaluation took >10s, the issue is likely kernel startup.")
    print("If subsequent evaluations are also slow, there may be a configuration issue.")

if __name__ == "__main__":
    test_wolfram_performance()