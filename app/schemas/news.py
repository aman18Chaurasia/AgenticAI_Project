from typing import Optional, List
from pydantic import BaseModel, HttpUrl


class NewsIn(BaseModel):
    source: str
    title: str
    url: HttpUrl
    published_at: str
    content: str


class NewsOut(BaseModel):
    id: int
    source: str
    title: str
    url: str
    published_at: str
    summary: Optional[str] = None


class CapsuleOut(BaseModel):
    date: str
    items: List[dict]

