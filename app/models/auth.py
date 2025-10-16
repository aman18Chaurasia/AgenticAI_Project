from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class SubscriptionRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    full_name: str
    reason: str  # Why they want to subscribe
    status: str = Field(default="pending")  # pending, approved, rejected
    requested_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    reviewed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[str] = None

class LoginAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    ip_address: str
    success: bool
    attempted_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    token: str = Field(unique=True)
    expires_at: str
    used: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())