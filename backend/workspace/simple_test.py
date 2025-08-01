#!/usr/bin/env python3
"""
Simple test file for AfterIDE - no external dependencies
"""

import os
import sys
from datetime import datetime

def main():
    print("🚀 Simple Test Script for AfterIDE")
    print("=" * 40)
    
    # Basic Python operations
    print(f"Python version: {sys.version}")
    print(f"Current time: {datetime.now()}")
    print(f"Current directory: {os.getcwd()}")
    
    # Simple calculations
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    average = total / len(numbers)
    
    print(f"\n📊 Calculations:")
    print(f"Numbers: {numbers}")
    print(f"Sum: {total}")
    print(f"Average: {average:.2f}")
    
    # List comprehension
    squares = [x**2 for x in numbers]
    print(f"Squares: {squares}")
    
    # Dictionary operations
    person = {
        "name": "AfterIDE User",
        "age": 25,
        "skills": ["Python", "JavaScript", "React"]
    }
    
    print(f"\n👤 Person data:")
    for key, value in person.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main() 