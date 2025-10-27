from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session
from .db import get_session
from .security import decode_access_token
from ..models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    session: Session = Depends(get_session),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(creds.credentials)
        uid = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    session: Session = Depends(get_session),
) -> Optional[User]:
    try:
        if not creds or creds.scheme.lower() != "bearer":
            return None
        payload = decode_access_token(creds.credentials)
        uid = int(payload.get("sub"))
        user = session.get(User, uid)
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None
