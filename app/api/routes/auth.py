from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import jwt
from ...core.db import get_session
from ...core.config import get_settings
from ...core.security import verify_password, get_password_hash
from ...models.user import User
from ...models.auth import SubscriptionRequest, LoginAttempt
from ...schemas.auth import LoginRequest, SubscriptionRequestCreate, TokenResponse

router = APIRouter()
security = HTTPBearer()
settings = get_settings()

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, req: Request, session: Session = Depends(get_session)):
    # Log attempt
    attempt = LoginAttempt(
        email=request.email,
        ip_address=req.client.host,
        success=False
    )
    
    user = session.exec(select(User).where(User.email == request.email)).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        session.add(attempt)
        session.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        session.add(attempt)
        session.commit()
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    # Success
    attempt.success = True
    user.last_login = datetime.now().isoformat()
    session.add(attempt)
    session.add(user)
    session.commit()
    
    # Create JWT token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    }
    token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)
    
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@router.post("/request-subscription")
def request_subscription(request: SubscriptionRequestCreate, session: Session = Depends(get_session)):
    # Check if already exists
    existing = session.exec(
        select(SubscriptionRequest).where(SubscriptionRequest.email == request.email)
    ).first()
    
    if existing and existing.status == "pending":
        raise HTTPException(status_code=400, detail="Request already pending")
    
    existing_user = session.exec(select(User).where(User.email == request.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    sub_request = SubscriptionRequest(
        email=request.email,
        full_name=request.full_name,
        reason=request.reason
    )
    session.add(sub_request)
    session.commit()
    
    return {"message": "Subscription request submitted. Admin will review shortly."}

class ForgotBody(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(body: ForgotBody, session: Session = Depends(get_session)):
    email = str(body.email).lower().strip()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return {"message": "If account exists, password reset instructions sent to email"}
    
    # Generate reset token
    import secrets
    from datetime import datetime, timedelta
    from ...models.auth import PasswordResetToken
    
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    
    # Save reset token
    reset_token = PasswordResetToken(
        email=email,
        token=token,
        expires_at=expires_at
    )
    session.add(reset_token)
    session.commit()
    
    # Send reset email
    from ...services.notifier import send_password_reset_email
    reset_link = f"http://localhost:8000/reset-password?token={token}"
    send_password_reset_email(email, reset_link)
    
    return {"message": "Password reset link sent to your email"}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, session: Session = Depends(get_session)):
    from ...models.auth import PasswordResetToken
    from datetime import datetime
    
    # Find valid token
    reset_token = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.token == request.token,
            PasswordResetToken.used == False
        )
    ).first()
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check expiration
    if datetime.fromisoformat(reset_token.expires_at) < datetime.now():
        raise HTTPException(status_code=400, detail="Token expired")
    
    # Update password
    user = session.exec(select(User).where(User.email == reset_token.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from ...core.security import get_password_hash
    user.hashed_password = get_password_hash(request.new_password)
    
    # Mark token as used
    reset_token.used = True
    
    session.add(user)
    session.add(reset_token)
    session.commit()
    
    return {"message": "Password reset successfully"}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload.get("sub"))
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(user: User = Depends(get_current_user)):
    if user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
