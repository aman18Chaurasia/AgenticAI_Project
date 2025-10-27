from datetime import date
import json
import os
from sqlmodel import Session, select
from ..models.content import NewsItem, Capsule, Mapping, SyllabusTopic
from .mapping import find_related_pyqs
from .summarizer import summarize_text, summarize_news_article


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
        # Get mappings for this news item (deduplicate by topic, keep top score)
        maps = session.exec(select(Mapping).where(Mapping.news_id == (n.id or 0))).all()
        topic_scores = {}
        for m in maps:
            topic = session.get(SyllabusTopic, m.topic_id)
            if not topic:
                continue
            key = (topic.paper, topic.topic)
            prev = topic_scores.get(key, 0.0)
            if float(m.score) > prev:
                topic_scores[key] = float(m.score)
        topics = [
            {"paper": p, "topic": t, "score": s}
            for (p, t), s in sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        
        # Get related PYQs with better context
        search_text = f"{n.title} {n.summary or n.content or ''}"
        # Add topic keywords for better matching
        try:
            topic_keywords = " ".join([t.get("topic", "") for t in topics]) if topics else ""
            enhanced_search = f"{search_text} {topic_keywords}"
        except:
            enhanced_search = search_text
        pyqs = find_related_pyqs(session, enhanced_search)
        
        # Build a clean, bullet-style summary at render time (always bulletize)
        base_text = (n.content or n.summary or "").strip()
        # If too short, try on-the-fly extraction for better summary
        if len(base_text) < 120:
            try:
                from .content_extract import extract_article_text
                extracted = extract_article_text(n.url)
                if extracted and len(extracted) > 160:
                    base_text = extracted
            except Exception:
                pass
        if base_text:
            try:
                summary = summarize_news_article(n.title, base_text, url=n.url)
            except Exception:
                summary = summarize_text(base_text, max_sentences=8)
        else:
            summary = "No summary available."
        # Drop heading line if it duplicates the title for cleaner display
        try:
            lines = [ln for ln in summary.splitlines() if ln.strip()]
            if lines and (n.title.lower() in lines[0].lower()) and ("key points" in lines[0].lower()):
                summary = "\n".join(lines[1:]).strip() or summary
        except Exception:
            pass
        
        items.append({
            "title": n.title,
            "url": n.url,
            "summary": summary,
            "topics": topics,
            "pyqs": [dict(t) for i, t in enumerate(pyqs) if t not in pyqs[:i]],
            "pyq_count": len([dict(t) for i, t in enumerate(pyqs) if t not in pyqs[:i]]),
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

