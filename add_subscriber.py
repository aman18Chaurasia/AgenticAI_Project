#!/usr/bin/env python3
"""
Script to add test subscribers for daily capsule
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.user import User

def add_test_subscriber(email: str, name: str):
    with Session(engine) as session:
        # Check if user already exists
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            print(f"User {email} already exists")
            return
        
        # Create new user with simple password hash
        user = User(
            email=email,
            full_name=name,
            hashed_password="$2b$12$dummy_hash_for_testing",  # Simple dummy hash
            role="student",
            daily_capsule_subscribed=True,
            weekly_report_subscribed=True
        )
        
        session.add(user)
        session.commit()
        print(f"Added subscriber: {name} ({email})")

def main():
    print("Adding test subscribers...")
    
    # Add some test subscribers
    test_users = [
        ("test@example.com", "Test User"),
        ("upsc.aspirant@gmail.com", "UPSC Aspirant"),
        ("student@civicbriefs.ai", "Demo Student")
    ]
    
    for email, name in test_users:
        add_test_subscriber(email, name)
    
    print(f"\nAdded {len(test_users)} test subscribers")
    print("To add your own email, edit this script or use the API endpoint")

if __name__ == "__main__":
    main()