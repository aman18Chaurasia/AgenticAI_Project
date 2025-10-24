from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from typing import Dict, Optional
from pydantic import BaseModel
from ...core.db import get_session
from ...services.chat import get_pyq_answer, chat_with_pyq

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/pyq/{question_id}")
def get_answer(question_id: int, session: Session = Depends(get_session)) -> Dict:
    """Get answer framework for a specific PYQ question"""
    result = get_pyq_answer(session, question_id)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result


class AskBody(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/ask")
async def ask_question(body: AskBody, req: Request, session: Session = Depends(get_session)) -> Dict:
    """Chat interface with history and retrieval grounding"""
    user_query = (body.question or "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Question is required")
    sess_key = body.session_id or (f"{req.client.host}" if req.client else None)
    return await chat_with_pyq(session, user_query, user_id=None, session_key=sess_key)
