#!/usr/bin/env python3
"""
Test script for AfterIDE Terminal functionality
"""

import asyncio
import sys
import os

def test_basic_commands():
    """Test basic command execution"""
    print("Testing basic commands...")
    
    # Test ls command
    try:
        result = os.listdir('.')
        print(f"ls output: {result}")
    except Exception as e:
        print(f"ls error: {e}")
    
    # Test pwd command
    try:
        result = os.getcwd()
        print(f"pwd output: {result}")
    except Exception as e:
        print(f"pwd error: {e}")

def test_python_execution():
    """Test Python code execution"""
    print("\nTesting Python execution...")
    
    # Simple Python code
    code = """
print("Hello from Python!")
print("Current directory:", os.getcwd())
print("Python version:", sys.version)
"""
    
    try:
        exec(code)
        print("Python execution successful")
    except Exception as e:
        print(f"Python execution error: {e}")

def test_file_operations():
    """Test file operations"""
    print("\nTesting file operations...")
    
    # Create a test file
    test_file = "test_output.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("This is a test file created by AfterIDE terminal\n")
        print(f"Created test file: {test_file}")
        
        # Read the file
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"File content: {content.strip()}")
        
        # Clean up
        os.remove(test_file)
        print(f"Removed test file: {test_file}")
        
    except Exception as e:
        print(f"File operation error: {e}")

def main():
    """Main test function"""
    print("=== AfterIDE Terminal Test ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print()
    
    test_basic_commands()
    test_python_execution()
    test_file_operations()
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main() 