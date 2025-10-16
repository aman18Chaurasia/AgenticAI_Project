#!/usr/bin/env python3
"""
Script to run the full CivicBriefs.ai pipeline with real feeds
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.orchestrator import run_once
from app.core.db import engine
from sqlmodel import SQLModel

def main():
    print("Starting CivicBriefs.ai Full Pipeline...")
    print("=" * 50)
    
    # Ensure database is initialized
    SQLModel.metadata.create_all(engine)
    print("Database initialized")
    
    # Run the full pipeline
    print("\nRunning full agentic pipeline...")
    try:
        run_once()
        print("\nPipeline completed successfully!")
        print("\nCheck your email for the daily capsule (if SMTP is configured)")
        print("Visit http://localhost:8000/capsule/daily to see the web version")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())