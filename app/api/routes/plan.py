from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...core.db import get_session
from ...core.deps import get_current_user
from ...models.user import User, StudyPlan, TestResult
from ...services.planner import adapt_plan_with_feedback, generate_plan_for_user
import json


router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("/me")
def get_my_plan(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    plan = session.exec(select(StudyPlan).where(StudyPlan.user_id == user.id)).first()
    if not plan:
        return {"plan": None}
    try:
        data = json.loads(plan.plan_json)
    except Exception:
        data = {"raw": plan.plan_json}
    return {"plan": data}


@router.post("/test-result")
def submit_test_result(payload: dict, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    name = (payload.get("test_name") or "Mock Test").strip()
    score = float(payload.get("score") or 0)
    tr = TestResult(user_id=user.id, test_name=name, score=score, date=payload.get("date") or "")
    session.add(tr)
    session.commit()
    adapt_plan_with_feedback(session, user.id)
    return {"message": "Recorded", "score": score}


@router.post("/recompute")
def recompute_plan(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Ensure a baseline plan exists
    plan = session.exec(select(StudyPlan).where(StudyPlan.user_id == user.id)).first()
    if not plan:
        generate_plan_for_user(session, user.id)
    # Re-run adaptation based on existing tests
    adapt_plan_with_feedback(session, user.id)
    plan = session.exec(select(StudyPlan).where(StudyPlan.user_id == user.id)).first()
    data = json.loads(plan.plan_json) if plan else None
    return {"message": "Recomputed", "plan": data}
