from datetime import date, timedelta
import json
from typing import Dict, List
from sqlmodel import Session, select
from ..models.content import Capsule
from ..models.user import TestResult, User


def _date_strs(days: int = 7) -> List[str]:
    today = date.today()
    return [str(today - timedelta(days=i)) for i in range(days)]


def build_weekly_report(session: Session) -> Dict:
    days = _date_strs(7)
    # Fetch capsules for last 7 days
    caps = (
        session.exec(select(Capsule).where(Capsule.date.in_(days))).all()
        or []
    )
    highlights: List[Dict] = []
    for c in caps:
        try:
            items = json.loads(c.items_json)
        except Exception:
            items = []
        for it in items[:3]:  # take top 3 per day
            highlights.append({
                "date": c.date,
                "title": it.get("title"),
                "url": it.get("url"),
                "summary": it.get("summary"),
                "topics": it.get("topics", []),
                "pyqs": it.get("pyqs", [])
            })

    # Simple progress summary across users (avg score last week)
    tests = session.exec(select(TestResult)).all() or []
    if tests:
        avg = sum(t.score for t in tests) / max(1, len(tests))
    else:
        avg = 0.0

    report = {
        "week_end": str(date.today()),
        "week_start": str(date.today() - timedelta(days=6)),
        "highlights": highlights[:30],  # cap
        "progress": {
            "tests_recorded": len(tests),
            "average_score": round(avg, 2),
        },
    }
    return report

