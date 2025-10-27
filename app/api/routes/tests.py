from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ...core.db import get_session
from ...core.deps import get_current_user_optional
from ...models.user import User
from ...services.tests import generate_daily_quiz, record_test_result, get_progress_summary, get_test_history


router = APIRouter(prefix="/tests", tags=["tests"])


@router.post("/generate/daily")
def generate_daily(force: bool = False, session: Session = Depends(get_session)) -> Dict[str, Any]:
    return generate_daily_quiz(session, force=force)


@router.get("/today")
def get_today(session: Session = Depends(get_session)) -> Dict[str, Any]:
    return generate_daily_quiz(session)


@router.post("/submit")
def submit_answers(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    user: User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    name = payload.get("name")
    answers: List[int] = payload.get("answers", [])
    if not name:
        raise HTTPException(status_code=400, detail="Missing test name")
    return record_test_result(session, user.id or 0, name, answers)


@router.get("/progress")
def progress(session: Session = Depends(get_session), user: User | None = Depends(get_current_user_optional)) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return get_progress_summary(session, user.id or 0)


@router.get("/history")
def history(session: Session = Depends(get_session), user: User | None = Depends(get_current_user_optional)) -> List[Dict[str, Any]]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return get_test_history(session, user.id or 0)
