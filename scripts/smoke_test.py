import os
import sys
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app


def main():
    client = TestClient(app)

    health = client.get("/health")
    print("/health:", health.status_code, health.json())

    capsule = client.get("/capsule/daily")
    print("/capsule/daily:", capsule.status_code)
    try:
        print(capsule.json())
    except Exception:
        print("No JSON body returned")

    schedule = client.post("/schedule/generate")
    print("/schedule/generate:", schedule.status_code, schedule.json())


if __name__ == "__main__":
    main()
