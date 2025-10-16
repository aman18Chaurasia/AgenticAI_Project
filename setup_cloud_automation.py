#!/usr/bin/env python3
"""
Setup cloud automation for CivicBriefs.ai
"""
import os
import subprocess
import sys

def setup_github_automation():
    print("🌐 Setting up GitHub Cloud Automation")
    print("=" * 40)
    
    # Check if git is initialized
    if not os.path.exists('.git'):
        print("📁 Initializing Git repository...")
        subprocess.run(['git', 'init'])
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Initial commit - Autonomous UPSC System'])
        subprocess.run(['git', 'branch', '-M', 'main'])
    
    print("\n📋 Next Steps:")
    print("1. Create a new repository on GitHub")
    print("2. Copy this command and run it:")
    print(f"   git remote add origin https://github.com/YOUR_USERNAME/civicbriefs-ai.git")
    print(f"   git push -u origin main")
    print("\n3. Go to GitHub → Actions tab")
    print("4. The workflow will run daily at 6:00 AM automatically!")
    print("\n✅ Your system will run in the cloud - PC can be off!")

def check_requirements():
    print("🔍 Checking system requirements...")
    
    # Check if all files exist
    required_files = [
        '.github/workflows/daily-pipeline.yml',
        'app/agents/orchestrator.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    print("🤖 CivicBriefs.ai - Cloud Automation Setup")
    print("=" * 50)
    
    if not check_requirements():
        print("❌ Setup incomplete. Please ensure all files are present.")
        return
    
    choice = input("""
Choose deployment option:
1. GitHub Actions (FREE - Recommended)
2. Show deployment guide
3. Test pipeline locally first
4. Exit

Enter choice (1-4): """).strip()
    
    if choice == "1":
        setup_github_automation()
    elif choice == "2":
        print("\n📖 See deploy_to_cloud.md for detailed instructions")
    elif choice == "3":
        print("\n🧪 Testing pipeline locally...")
        subprocess.run([sys.executable, "-m", "app.agents.orchestrator", "--run-once"])
    elif choice == "4":
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")

if __name__ == "__main__":
    main()