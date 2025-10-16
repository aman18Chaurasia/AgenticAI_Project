import json
from datetime import date
from sqlmodel import Session, select
from ..models.user import StudyPlan, User, TestResult
from ..models.content import SyllabusTopic


def generate_plan_for_default_user(session: Session) -> None:
    user = session.exec(select(User)).first()
    if not user:
        user = User(email="student@example.com", full_name="Student", hashed_password="", role="student")
        session.add(user)
        session.commit()
        session.refresh(user)
    topics = session.exec(select(SyllabusTopic)).all()
    chunks = [t.topic for t in topics][:20]
    plan = {
        "generated_on": str(date.today()),
        "weeks": [
            {"week": 1, "hours": 10, "tasks": chunks[:10]},
            {"week": 2, "hours": 10, "tasks": chunks[10:20]},
        ],
    }
    existing = session.exec(select(StudyPlan).where(StudyPlan.user_id == (user.id or 0))).first()
    if existing:
        existing.plan_json = json.dumps(plan)
        session.add(existing)
    else:
        session.add(StudyPlan(user_id=user.id or 0, target_year=date.today().year, available_hours_per_week=10, plan_json=json.dumps(plan)))
    session.commit()


def adapt_plan_with_feedback(session: Session, user_id: int) -> None:
    tests = session.exec(select(TestResult).where(TestResult.user_id == user_id)).all()
    if not tests:
        return
    # Placeholder: adjust available hours up/down based on average score
    avg = sum(t.score for t in tests) / max(1, len(tests))
    plan = session.exec(select(StudyPlan).where(StudyPlan.user_id == user_id)).first()
    if plan:
        obj = json.loads(plan.plan_json)
        for w in obj.get("weeks", []):
            w["hours"] = max(6, min(18, int(w.get("hours", 10) * (0.9 if avg > 70 else 1.1))))
        plan.plan_json = json.dumps(obj)
        session.add(plan)
        session.commit()

