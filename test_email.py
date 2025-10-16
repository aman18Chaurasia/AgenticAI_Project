#!/usr/bin/env python3
"""
Test email functionality with a simple test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.notifier import send_daily_capsule_email

def test_email():
    # Test capsule data
    test_capsule = {
        "date": "2025-10-14",
        "items": [
            {
                "title": "Test News Article",
                "url": "https://example.com/news1",
                "summary": "This is a test summary of the news article.",
                "topics": [
                    {"paper": "GS1", "topic": "Indian History", "score": 0.85}
                ],
                "pyqs": [
                    {"question": "Test PYQ Question?", "year": "2023"}
                ]
            }
        ]
    }
    
    print("Testing email functionality...")
    print("Note: This will only work if you have configured Gmail App Password in .env")
    
    # Try to send test email
    result = send_daily_capsule_email("test@example.com", test_capsule)
    
    if result:
        print("Email sent successfully!")
    else:
        print("Email failed - check your SMTP configuration")
        print("\nTo fix email issues:")
        print("1. Go to your Google Account settings")
        print("2. Enable 2-Factor Authentication")
        print("3. Generate an App Password for 'Mail'")
        print("4. Update SMTP_PASSWORD in .env with the App Password")

if __name__ == "__main__":
    test_email()