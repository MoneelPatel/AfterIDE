"""
Application module
"""

class App:
    def __init__(self):
        self.name = "My Application"
    
    def run(self):
        print(f"Running {self.name}")
        return "Application started successfully" 