from typing import List, Dict
from sqlmodel import Session, select
from ..models.content import NewsItem, SyllabusTopic, Mapping, PyqQuestion
from .semantic import tfidf_similarity
from .summarizer import simple_summarize


def map_news_to_syllabus(session: Session) -> int:
    news = session.exec(select(NewsItem)).all()
    topics = session.exec(select(SyllabusTopic)).all()
    if not news or not topics:
        return 0
    topic_corpus = [f"{t.paper} {t.topic} {t.keywords or ''}" for t in topics]
    created = 0
    for n in news:
        if not n.summary:
            n.summary = simple_summarize(n.content)
            session.add(n)
            session.commit()
        ranked = tfidf_similarity(f"{n.title} {n.summary}", topic_corpus)[:3]
        for idx, score in ranked:
            m = Mapping(news_id=n.id or 0, topic_id=topics[idx].id or 0, score=float(score))
            session.add(m)
            created += 1
        session.commit()
    return created


def find_related_pyqs(session: Session, text: str, top_k: int = 3) -> List[Dict]:
    pyqs = session.exec(select(PyqQuestion)).all()
    corpus = [f"{p.paper} {p.year} {p.question} {p.keywords or ''}" for p in pyqs]
    ranked = tfidf_similarity(text, corpus)[:top_k]
    out: List[Dict] = []
    for idx, score in ranked:
        p = pyqs[idx]
        out.append({"id": p.id, "year": p.year, "paper": p.paper, "question": p.question, "score": float(score)})
    return out

