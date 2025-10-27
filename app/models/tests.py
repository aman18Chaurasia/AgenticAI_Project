from typing import Optional
from sqlmodel import Field, SQLModel


class GeneratedTest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    name: str = Field(index=True)
    questions_json: str  # serialized list of questions with options/answers if available

