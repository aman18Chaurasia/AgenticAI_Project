#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.core.db import engine
from app.services.capsules import build_daily_capsule

def test_capsule():
    try:
        with Session(engine) as session:
            result = build_daily_capsule(session)
            print(f"Success! Found {len(result['items'])} items")
            
            # Show first item's PYQs
            if result['items']:
                first_item = result['items'][0]
                print(f"\nFirst item: {first_item['title']}")
                print(f"PYQs: {len(first_item['pyqs'])}")
                for pyq in first_item['pyqs'][:2]:
                    print(f"  - {pyq['question']} ({pyq['year']}) - Score: {pyq['score']}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_capsule()