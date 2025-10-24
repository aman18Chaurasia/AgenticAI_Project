from typing import Dict, Optional, List
import httpx
from sqlmodel import Session, select
from ..models.content import PyqQuestion, NewsItem
from ..models.chat import ChatMessage
from .semantic import tfidf_similarity


def get_pyq_answer(session: Session, question_id: int) -> Optional[Dict]:
    pyq = session.get(PyqQuestion, question_id)
    if not pyq:
        return None
    answer = f"Intro → key points with current examples → conclusion for {pyq.paper} {pyq.year}."
    return {
        "question_id": question_id,
        "question": pyq.question,
        "paper": pyq.paper,
        "year": pyq.year,
        "answer": answer,
        "keywords": pyq.keywords,
    }


def _clean_ai(text: str) -> str:
    lines = [ln for ln in (text or "").splitlines() if not ln.strip().startswith(("User:", "Assistant:"))]
    out = "\n".join(lines).strip()
    # remove surrounding quotes/backticks
    if (out.startswith('"') and out.endswith('"')) or (out.startswith("'") and out.endswith("'")):
        out = out[1:-1].strip()
    out = out.replace('\uFFFD', '').strip()
    return out


async def get_ai_response(question: str, context: str = "") -> str:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prompt = f"Question: {question}\nContext: {context[:1200]}\nAnswer clearly and accurately:"
            r = await client.post(
                "https://api-inference.huggingface.co/models/google/flan-t5-base",
                headers={"Content-Type": "application/json"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 200}}
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    txt = data[0].get('generated_text') or data[0].get('summary_text')
                    if txt:
                        return _clean_ai(txt)
                if isinstance(data, dict) and 'generated_text' in data:
                    return _clean_ai(str(data['generated_text']))
    except Exception as e:
        print(f"AI API error: {e}")
    fb = (context[:200] + " ...") if context else "Please specify details so I can tailor a UPSC-ready answer."
    return _clean_ai(fb)


def _save_message(session: Session, role: str, content: str, user_id: Optional[int] = None, session_id: Optional[str] = None) -> None:
    session.add(ChatMessage(role=role, content=content, user_id=user_id, session_id=session_id))
    session.commit()


def _get_history(session: Session, user_id: Optional[int], session_id: Optional[str], limit: int = 6) -> List[ChatMessage]:
    q = select(ChatMessage)
    if user_id is not None:
        q = q.where(ChatMessage.user_id == user_id)
    elif session_id:
        q = q.where(ChatMessage.session_id == session_id)
    else:
        return []
    q = q.order_by(ChatMessage.id.desc())
    items = session.exec(q).all()
    return list(reversed(items[-limit:])) if items else []


def _build_context_from_history(history: List[ChatMessage]) -> str:
    parts = []
    for m in history[-6:]:
        prefix = "User:" if m.role == 'user' else "Assistant:"
        parts.append(f"{prefix} {m.content}")
    return "\n".join(parts[-6:])


def _retrieve_relevant_facts(session: Session, question: str, top_k: int = 3):
    news = session.exec(select(NewsItem)).all() or []
    corpus = [f"{n.title} {n.summary or ''} {n.content or ''}" for n in news]
    ranked = tfidf_similarity(question, corpus)[:top_k]
    facts = []
    for idx, score in ranked:
        n = news[idx]
        facts.append({"title": n.title, "summary": (n.summary or n.content or "")[:300], "url": n.url, "score": float(score)})
    pyqs_all = session.exec(select(PyqQuestion)).all() or []
    pyq_corpus = [f"{p.paper} {p.year} {p.question} {p.keywords or ''}" for p in pyqs_all]
    pyq_ranked = tfidf_similarity(question, pyq_corpus)[:top_k]
    pyqs = []
    for idx, score in pyq_ranked:
        p = pyqs_all[idx]
        pyqs.append({"year": p.year, "paper": p.paper, "question": p.question, "score": float(score)})
    context = "\n".join([f"- {f['title']}: {f['summary']}" for f in facts])
    return context, pyqs


async def chat_with_pyq(session: Session, user_query: str, user_id: Optional[int] = None, session_key: Optional[str] = None) -> Dict:
    qtext = (user_query or "").strip()
    qlow = qtext.lower()

    # Fast path: greetings / small talk without model
    if any(g in qlow for g in ["hi", "hii", "hello", "hey", "hey there", "what's up", "whats up"]):
        msg = (
            "Hi! I’m your UPSC mentor. Ask me about current affairs, "
            "map a topic to GS papers, or request PYQs (e.g., ‘Map RBI inflation update’ "
            "or ‘PYQs on biodiversity’)."
        )
        _save_message(session, 'user', qtext, user_id=user_id, session_id=session_key)
        _save_message(session, 'assistant', msg, user_id=user_id, session_id=session_key)
        return {"response": msg}

    # Fast path: news digest from stored items when user mentions news
    if "news" in qlow:
        items: List[NewsItem] = session.exec(select(NewsItem)).all() or []
        recent = items[-5:][::-1]
        if not recent:
            digest = "No news stored yet. Run the pipeline or add sample news."
        else:
            bullets = [f"- {n.title} — {n.source}" for n in recent]
            digest = "Here are the latest items:\n" + "\n".join(bullets)
        _save_message(session, 'user', qtext, user_id=user_id, session_id=session_key)
        _save_message(session, 'assistant', digest, user_id=user_id, session_id=session_key)
        return {"response": digest}

    history = _get_history(session, user_id, session_key, limit=6)
    hist_ctx = _build_context_from_history(history)
    fact_ctx, pyqs_rel = _retrieve_relevant_facts(session, user_query, top_k=3)
    full_ctx = (hist_ctx + "\n\n" + fact_ctx).strip()

    response = await get_ai_response(user_query, full_ctx)
    # De-duplicate repeated lines and trim overly long answers
    if response:
        lines = [ln.strip() for ln in response.splitlines() if ln.strip()]
        seen = set()
        dedup = []
        for ln in lines:
            key = ln.lower()
            if key in seen:
                continue
            seen.add(key)
            dedup.append(ln)
        response = "\n".join(dedup[:12])
        if len(response) > 1200:
            response = response[:1200] + "…"
    if not response:
        response = "I didn't catch that. Could you rephrase or add specifics?"
    _save_message(session, 'user', user_query, user_id=user_id, session_id=session_key)
    _save_message(session, 'assistant', response, user_id=user_id, session_id=session_key)

    out = {"response": response}
    ql = user_query.lower()
    if any(k in ql for k in ['governance','economy','foreign policy','constitution','polity','environment','security','ethics']) and pyqs_rel:
        out["pyqs"] = pyqs_rel[:3]
    return out
