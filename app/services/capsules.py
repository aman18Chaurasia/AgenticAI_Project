from datetime import date
import json
from sqlmodel import Session, select
from ..models.content import NewsItem, Capsule, Mapping, SyllabusTopic
from .mapping import find_related_pyqs


def build_daily_capsule(session: Session):
    today = str(date.today())
    existing = session.exec(select(Capsule).where(Capsule.date == today)).first()
    if existing:
        items = json.loads(existing.items_json)
        if items:  # Only return if capsule has content
            return {"date": today, "items": items}
    
    # Get latest 15 news items
    news = session.exec(select(NewsItem)).all()[-15:]
    items = []
    
    for n in news:
        # Get mappings for this news item
        maps = session.exec(select(Mapping).where(Mapping.news_id == (n.id or 0))).all()
        topics = []
        for m in maps:
            topic = session.get(SyllabusTopic, m.topic_id)
            if topic:
                topics.append({"paper": topic.paper, "topic": topic.topic, "score": m.score})
        
        # Get related PYQs with better context
        search_text = f"{n.title} {n.summary or n.content or ''}"
        # Add topic keywords for better matching
        try:
            topic_keywords = " ".join([t.get("topic", "") for t in topics]) if topics else ""
            enhanced_search = f"{search_text} {topic_keywords}"
        except:
            enhanced_search = search_text
        pyqs = find_related_pyqs(session, enhanced_search)
        
        # Use content as summary if summary is empty
        summary = n.summary or n.content or "No summary available"
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        items.append({
            "title": n.title,
            "url": n.url,
            "summary": summary,
            "topics": topics,
            "pyqs": pyqs,
            "pyq_count": len(pyqs),
            "relevance_score": max([p["score"] for p in pyqs]) if pyqs else 0.0
        })
    
    # Save new capsule
    if existing:
        existing.items_json = json.dumps(items)
        session.add(existing)
    else:
        cap = Capsule(date=today, items_json=json.dumps(items))
        session.add(cap)
    
    session.commit()
    return {"date": today, "items": items}

