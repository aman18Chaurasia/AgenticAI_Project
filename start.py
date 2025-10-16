#!/usr/bin/env python3
"""
Complete startup script for CivicBriefs.ai
"""
import sys
import os
import subprocess
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("Starting CivicBriefs.ai - UPSC Preparation Mentor")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    try:
        subprocess.run([sys.executable, "-m", "app.main", "--init-db"], check=True)
        print("Database initialized")
    except subprocess.CalledProcessError:
        print("Database initialization failed")
        return 1
    
    # Step 2: Add subscribers
    print("\n2. Adding test subscribers...")
    try:
        subprocess.run([sys.executable, "add_subscriber.py"], check=True)
        print("Test subscribers added")
    except subprocess.CalledProcessError:
        print("Failed to add subscribers")
    
    # Step 3: Run pipeline
    print("\n3. Running initial pipeline...")
    try:
        subprocess.run([sys.executable, "run_pipeline.py"], check=True)
        print("Pipeline completed")
    except subprocess.CalledProcessError:
        print("Pipeline failed")
    
    # Step 4: Start server
    print("\n4. Starting web server...")
    print("Frontend will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped. Goodbye!")
        return 0

if __name__ == "__main__":
    exit(main())