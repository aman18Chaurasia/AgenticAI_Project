from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from ...core.db import get_session
from ...models.user import User
from ...models.auth import PasswordResetToken
from ...services.notifier import send_password_reset_email


router = APIRouter(prefix="/auth", tags=["auth"]) 


class ForgotIn(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(payload: ForgotIn, session: Session = Depends(get_session)):
    email = str(payload.email).lower().strip()
    user = session.exec(select(User).where(User.email == email)).first()
    # Always respond success to avoid user enumeration
    if not user:
        return {"message": "If the account exists, a reset link was sent."}
    # Create token valid for 1 hour
    token = __import__("secrets").token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    prt = PasswordResetToken(email=email, token=token, expires_at=expires_at, used=False)
    session.add(prt)
    session.commit()
    # Send link to reset page on this server
    link = f"http://localhost:8000/reset-password?token={token}"
    send_password_reset_email(email, link)
    return {"message": "If the account exists, a reset link was sent."}


class ResetIn(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
def reset_password(payload: ResetIn, session: Session = Depends(get_session)):
    prt = session.exec(select(PasswordResetToken).where(PasswordResetToken.token == payload.token)).first()
    if not prt or prt.used:
        raise HTTPException(status_code=400, detail="Invalid or used token")
    try:
        if datetime.fromisoformat(prt.expires_at) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=400, detail="Token expired")
    user = session.exec(select(User).where(User.email == prt.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from ...core.security import get_password_hash
    user.hashed_password = get_password_hash(payload.new_password)
    prt.used = True
    session.add(user)
    session.add(prt)
    session.commit()
    return {"message": "Password updated"}

