#!/usr/bin/env python3
"""
Simple test file for AfterIDE terminal
"""

print("Hello from AfterIDE!")
print("This file was created to test terminal functionality.")

# Simple calculation
result = 2 + 2
print(f"2 + 2 = {result}")

# List current directory
import os
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

print("Test completed successfully!") 