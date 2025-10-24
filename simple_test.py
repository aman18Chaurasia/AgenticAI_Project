#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.core.db import engine
from app.agents.news_agent import NewsAgent
from app.services.capsules import build_daily_capsule

def main():
    print("Testing news ingestion and capsule generation...")
    
    # Run news agent
    try:
        news_agent = NewsAgent()
        result = news_agent.run()
        print(f"News Agent: {result.success} - {result.detail}")
        
        # Test capsule generation
        with Session(engine) as session:
            capsule = build_daily_capsule(session)
            print(f"Capsule generated with {len(capsule['items'])} items")
            
            # Show first few PYQs
            if capsule['items']:
                first_item = capsule['items'][0]
                print(f"First item: {first_item['title'][:50]}...")
                print(f"PYQs found: {len(first_item['pyqs'])}")
                for i, pyq in enumerate(first_item['pyqs'][:3]):
                    print(f"  {i+1}. {pyq['question'][:60]}... ({pyq['year']}) Score: {pyq['score']:.3f}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()