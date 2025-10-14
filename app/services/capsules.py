from datetime import date
import json
from sqlmodel import Session, select
from ..models.content import NewsItem, Capsule, Mapping, SyllabusTopic
from .mapping import find_related_pyqs


def build_daily_capsule(session: Session):
    today = str(date.today())
    existing = session.exec(select(Capsule).where(Capsule.date == today)).first()
    if existing:
        return {"date": today, "items": json.loads(existing.items_json)}
    news = session.exec(select(NewsItem)).all()[-10:]
    items = []
    for n in news:
        maps = session.exec(select(Mapping).where(Mapping.news_id == (n.id or 0))).all()
        topics = []
        for m in maps:
            topic = session.get(SyllabusTopic, m.topic_id)
            if topic:
                topics.append({"paper": topic.paper, "topic": topic.topic, "score": m.score})
        pyqs = find_related_pyqs(session, f"{n.title} {n.summary or ''}")
        items.append({
            "title": n.title,
            "url": n.url,
            "summary": n.summary,
            "topics": topics,
            "pyqs": pyqs,
        })
    cap = Capsule(date=today, items_json=json.dumps(items))
    session.add(cap)
    session.commit()
    return {"date": today, "items": items}

