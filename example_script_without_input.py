#!/usr/bin/env python3
"""
Example script that avoids input() issues by using command line arguments
or environment variables instead of interactive input.
"""

import sys
import os

def main():
    print("Welcome to the input tester!")
    
    # Method 1: Use command line arguments
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "Default User"
    
    print(f"Hello, {name}!")
    
    # Method 2: Use environment variables
    age_str = os.environ.get('AGE', '25')
    try:
        age = int(age_str)
        if age < 0:
            print("You entered a negative age. That's suspicious.")
        elif age < 18:
            print("You're a minor.")
        else:
            print("You're an adult.")
    except ValueError:
        print("That doesn't look like a valid age.")
    
    likes_python = os.environ.get('LIKES_PYTHON', 'yes').strip().lower()
    if likes_python in ['yes', 'y']:
        print("Great! Python is awesome.")
    elif likes_python in ['no', 'n']:
        print("That's okay. Everyone has their preferences.")
    else:
        print("I didn't understand that answer.")

if __name__ == "__main__":
    main() 