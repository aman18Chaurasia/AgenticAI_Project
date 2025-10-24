from typing import Optional
from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True, foreign_key="user.id")
    session_id: Optional[str] = Field(default=None, index=True)
    role: str = Field(default="user")  # 'user' or 'assistant'
    content: str
    created_at: str = Field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())

