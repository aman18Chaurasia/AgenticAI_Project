from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

class SubscriptionRequestCreate(BaseModel):
    email: EmailStr
    full_name: str
    reason: str

class SubscriptionRequestOut(BaseModel):
    id: int
    email: str
    full_name: str
    reason: str
    status: str
    requested_at: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[str] = None