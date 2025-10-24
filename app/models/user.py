from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    hashed_password: str
    role: str = Field(default="user")  # user, admin, manager
    is_active: bool = Field(default=True)
    daily_capsule_subscribed: bool = Field(default=False)
    weekly_report_subscribed: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: __import__('datetime').datetime.now().isoformat())
    last_login: Optional[str] = None


class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    test_name: str
    score: float
    date: str


class StudyPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    target_year: int
    available_hours_per_week: int
    plan_json: str  # serialized plan


class UserSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    subscribed_date: str
    last_capsule_sent: Optional[str] = None

