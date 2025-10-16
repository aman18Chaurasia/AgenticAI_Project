from typing import Optional
from sqlmodel import Field, SQLModel


class NewsItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)
    title: str
    url: str = Field(index=True)
    published_at: str
    content: str
    summary: Optional[str] = None


class SyllabusTopic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper: str  # GS1|GS2|GS3|GS4
    topic: str
    keywords: Optional[str] = None


class PyqQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    paper: str
    question: str
    keywords: Optional[str] = None


class Mapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(index=True, foreign_key="newsitem.id")
    topic_id: int = Field(index=True, foreign_key="syllabustopic.id")
    score: float = 0.0


class Capsule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    items_json: str  # serialized capsule with links to news + topics + pyqs

