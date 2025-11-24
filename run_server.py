#!/usr/bin/env python
"""
Run Django server with ASGI support for WebSocket connections.
This script uses daphne to run the server with proper WebSocket support.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
    django.setup()
    
    # Try to use daphne if available, otherwise fallback to runserver
    try:
        import daphne
        print("Starting server with daphne (ASGI support for WebSockets)...")
        print("Server will be available at: http://127.0.0.1:8000")
        print("WebSocket endpoint: ws://127.0.0.1:8000/ws/chat/")
        print("\nPress CTRL+C to stop the server\n")
        
        from daphne.cli import CommandLineInterface
        sys.argv = ['daphne', '-b', '127.0.0.1', '-p', '8000', 'Project.asgi:application']
        CommandLineInterface().run()
    except ImportError:
        print("Warning: daphne not installed. Installing daphne for WebSocket support...")
        print("Run: pip install daphne")
        print("\nFalling back to runserver (WebSocket may not work)...")
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])


