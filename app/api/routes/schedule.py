from fastapi import APIRouter
from sqlmodel import Session
from ...core.db import engine
from ...schemas.common import Message
from ...services.planner import generate_plan_for_default_user

router = APIRouter()


@router.post("/generate", response_model=Message)
def generate_schedule():
    with Session(engine) as session:
        generate_plan_for_default_user(session)
    return Message(message="Schedule generated/updated")

