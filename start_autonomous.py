#!/usr/bin/env python3
"""
Start the autonomous UPSC preparation system
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("🤖 CivicBriefs.ai - Autonomous UPSC Preparation System")
    print("=" * 50)
    
    choice = input("""
Choose operation mode:
1. Run pipeline once (test)
2. Start daily scheduler (autonomous)
3. Start web server only
4. Exit

Enter choice (1-4): """).strip()
    
    if choice == "1":
        print("\n🔄 Running pipeline once...")
        subprocess.run([sys.executable, "-m", "app.agents.orchestrator", "--run-once"])
        
    elif choice == "2":
        print("\n🕕 Starting autonomous daily scheduler...")
        print("📅 Will run every day at 6:00 AM")
        print("🔄 Press Ctrl+C to stop")
        subprocess.run([sys.executable, "-m", "app.agents.orchestrator", "--schedule"])
        
    elif choice == "3":
        print("\n🌐 Starting web server...")
        subprocess.run(["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
        
    elif choice == "4":
        print("\n👋 Goodbye!")
        sys.exit(0)
        
    else:
        print("\n❌ Invalid choice. Please try again.")
        main()

if __name__ == "__main__":
    main()