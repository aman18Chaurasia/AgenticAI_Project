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


def extract_key_entities(text: str) -> List[str]:
    """Extract key entities and topics from news text"""
    # Simple keyword extraction based on common UPSC topics
    upsc_keywords = {
        'governance': ['government', 'policy', 'administration', 'bureaucracy', 'civil service'],
        'economy': ['economic', 'gdp', 'inflation', 'fiscal', 'monetary', 'trade', 'investment'],
        'international': ['foreign', 'diplomatic', 'bilateral', 'multilateral', 'treaty', 'agreement'],
        'security': ['defense', 'military', 'border', 'terrorism', 'cyber', 'national security'],
        'environment': ['climate', 'environment', 'pollution', 'renewable', 'biodiversity', 'conservation'],
        'social': ['education', 'health', 'poverty', 'inequality', 'welfare', 'rights'],
        'technology': ['digital', 'artificial intelligence', 'technology', 'innovation', 'startup'],
        'constitution': ['constitutional', 'fundamental rights', 'duties', 'amendment', 'judiciary']
    }
    
    text_lower = text.lower()
    found_topics = []
    
    for topic, keywords in upsc_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            found_topics.append(topic)
    
    return found_topics

def find_related_pyqs(session: Session, text: str, top_k: int = 3) -> List[Dict]:
    pyqs = session.exec(select(PyqQuestion)).all()
    if not pyqs:
        return []
    
    # Extract key topics from news
    news_topics = extract_key_entities(text)
    
    # Enhanced matching with topic relevance
    scored_pyqs = []
    
    for p in pyqs:
        # Base similarity score
        question_text = f"{p.question} {p.keywords or ''}"
        base_scores = tfidf_similarity(text, [question_text])
        base_score = base_scores[0][1] if base_scores else 0.0
        
        # Topic relevance bonus
        topic_bonus = 0.0
        pyq_topics = extract_key_entities(p.question + ' ' + (p.keywords or ''))
        common_topics = set(news_topics) & set(pyq_topics)
        if common_topics:
            topic_bonus = len(common_topics) * 0.2  # Bonus for topic match
        
        final_score = base_score + topic_bonus
        
        scored_pyqs.append({
            "id": p.id,
            "year": p.year,
            "paper": p.paper,
            "question": p.question,
            "score": float(final_score),
            "topics_matched": list(common_topics)
        })
    
    # Sort by score and return top matches
    scored_pyqs.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter out very low scores (< 0.05)
    relevant_pyqs = [p for p in scored_pyqs if p['score'] > 0.05][:top_k]
    
    # If no relevant matches, return top 3 with warning
    if not relevant_pyqs:
        relevant_pyqs = scored_pyqs[:top_k]
        for p in relevant_pyqs:
            p['score'] = 0.01  # Low confidence score
    
    return relevant_pyqs

