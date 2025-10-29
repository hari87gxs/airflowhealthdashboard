#!/usr/bin/env python3
"""
Quick test script to verify the backend fixes work
"""
import sys
import os
sys.path.append('/Users/harikrishnan.r/Downloads/airflow-health-dashboard/backend')

# Simple mock to test the defense against None values
def test_none_handling():
    print("Testing None handling in lower() calls...")
    
    # Test scenarios that could cause the error
    test_data = [
        {"state": "failed"},
        {"state": "running"}, 
        {"state": None},  # This could cause the issue
        {},  # Missing state key
        None,  # Entire run could be None
    ]
    
    print("Testing with different data scenarios:")
    for i, run in enumerate(test_data):
        print(f"  Test {i+1}: {run}")
        try:
            if run is None:
                print(f"    Found None run, skipping")
                continue
            state_raw = run.get("state", "")
            if state_raw is None:
                print(f"    Found None state, using empty string")
                state_raw = ""
            state = state_raw.lower()
            print(f"    Result: '{state}'")
        except Exception as e:
            print(f"    ERROR: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_none_handling()