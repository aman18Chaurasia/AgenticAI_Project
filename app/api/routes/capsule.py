from fastapi import APIRouter
from sqlmodel import Session
from ...core.db import engine
from ...schemas.news import CapsuleOut
from ...services.capsules import build_daily_capsule

router = APIRouter()


@router.get("/daily", response_model=CapsuleOut)
def daily_capsule():
    with Session(engine) as session:
        capsule = build_daily_capsule(session)
        return capsule

