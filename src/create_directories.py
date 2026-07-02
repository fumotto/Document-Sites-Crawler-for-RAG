import os

def create_directories():
    directories = ['cache', 'output', 'archives', 'logs']
    for dir in directories:
        os.makedirs(dir, exist_ok=True)
    print("Directories created successfully.")