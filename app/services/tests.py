import json
import os
import logging
from datetime import date
from typing import Dict, List, Any
import random
import httpx
from sqlmodel import Session, select
from ..models.content import Capsule, SyllabusTopic
from ..models.tests import GeneratedTest
from ..models.user import TestResult
from ..core.config import get_settings


logger = logging.getLogger(__name__)


def _default_quiz_name(d: date | None = None) -> str:
    today = d or date.today()
    return f"Daily Quiz - {today.isoformat()}"


def _build_questions_from_capsule(capsule: Dict[str, Any], all_topics: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Deterministic MCQs from capsule with sensible syllabus options.

    - Correct option = top-mapped syllabus topic from the item
    - Distractors = other plausible topics (different papers or related areas)
    """
    questions: List[Dict[str, Any]] = []

    def _topic_str(paper: str, topic: str) -> str:
        p = (paper or "GS").strip()
        t = (topic or "Syllabus").strip()
        return f"{p}: {t}"

    # Pre-build a pool of topic strings for distractors
    pool: List[str] = []
    for t in all_topics:
        pool.append(_topic_str(t.get("paper", "GS"), t.get("topic", "")))
    pool = list(dict.fromkeys(pool))  # unique

    for item in capsule.get("items", [])[:10]:
        title = item.get("title") or "Current Affairs"
        summary = item.get("summary") or ""
        mapped = item.get("topics", []) or []
        if mapped:
            # pick highest score mapping as correct
            best = sorted(mapped, key=lambda x: float(x.get("score", 0.0)), reverse=True)[0]
            correct_text = _topic_str(best.get("paper", "GS"), best.get("topic", ""))
        else:
            correct_text = "GS2: Polity & Governance"
        # pick 3 distractors different from correct
        distractors: List[str] = []
        for cand in pool:
            if cand != correct_text and cand not in distractors:
                distractors.append(cand)
            if len(distractors) >= 3:
                break
        options = [correct_text] + distractors
        # shuffle and compute correct index
        random.shuffle(options)
        ans_index = options.index(correct_text)
        stem = f"Which syllabus mapping best fits: {title}?"
        questions.append({
            "q": stem,
            "context": summary,
            "options": options[:4],
            "answer_index": ans_index,
            "explanation": "Correct mapping is derived from the highest-confidence syllabus link for this news item.",
            "source": item.get("url"),
        })
    return questions


def _llm_available() -> bool:
    settings = get_settings()
    return bool(settings.openai_api_key)


def _truncate(text: str, max_len: int = 800) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _build_llm_prompt(capsule: Dict[str, Any]) -> str:
    items = capsule.get("items", [])[:8]
    lines: List[str] = []
    for i, it in enumerate(items, start=1):
        topics = ", ".join([f"{t.get('paper','GS')}:{t.get('topic','')}" for t in (it.get("topics") or [])][:4])
        lines.append(
            f"{i}. Title: {it.get('title','')}. Summary: {_truncate(it.get('summary',''))}. Topics: {topics}. URL: {it.get('url','')}"
        )
    instructions = (
        "You are a UPSC mentor. Generate 8-10 MCQs for UPSC CSE based on the items. "
        "Rules: (1) Each option MUST be a specific UPSC syllabus mapping formatted 'GSx: Topic' (e.g., 'GS2: Federalism'). "
        "(2) Provide 4 unique options per question; exactly one correct. (3) Provide answer_index (0-3). "
        "(4) Include a short explanation tied to the syllabus and the news; (5) Include the source URL. "
        "Output STRICT JSON only: {\"questions\":[{\"q\":str,\"options\":[str,str,str,str],\"answer_index\":int,\"explanation\":str,\"source\":str}]}."
    )
    return instructions + "\nItems:\n" + "\n".join(lines)


def _generate_questions_with_llm(capsule: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not _llm_available():
        return []
    settings = get_settings()
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": "You are a precise UPSC mentor."},
            {"role": "user", "content": _build_llm_prompt(capsule)},
        ],
        "temperature": 0.4,
    }
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        obj = json.loads(content)
        questions = obj.get("questions") or []
        # Validate structure minimally
        cleaned: List[Dict[str, Any]] = []
        for q in questions[:10]:
            opts = q.get("options") or []
            if not isinstance(opts, list) or len(opts) < 2:
                continue
            ai = int(q.get("answer_index", 0))
            if ai < 0 or ai >= len(opts):
                ai = 0
            # normalize to 4 options and shuffle while keeping correct
            o4 = [str(o) for o in opts][:4]
            if len(o4) < 4:
                # simple padding to reach 4 options
                pads = ["GS2: Governance", "GS3: Economy", "GS1: Society", "GS4: Ethics"]
                for p in pads:
                    if len(o4) >= 4:
                        break
                    if p not in o4:
                        o4.append(p)
            correct_val = o4[ai] if ai < len(o4) else o4[0]
            random.shuffle(o4)
            new_ai = o4.index(correct_val)
            cleaned.append({
                "q": str(q.get("q", "Current Affairs")),
                "context": str(q.get("context", "")),
                "options": o4,
                "answer_index": new_ai,
                "explanation": str(q.get("explanation", "")),
                "source": str(q.get("source", "")),
            })
        return cleaned
    except Exception as exc:
        logger.warning("LLM quiz generation failed: %s", exc)
        return []


def generate_daily_quiz(session: Session, force: bool = False) -> Dict[str, Any]:
    today_str = date.today().isoformat()
    existing = session.exec(
        select(GeneratedTest).where(GeneratedTest.date == today_str, GeneratedTest.name == _default_quiz_name())
    ).first()
    if existing and not force:
        return {"date": existing.date, "name": existing.name, "questions": json.loads(existing.questions_json)}
    if existing and force:
        session.delete(existing)
        session.commit()

    cap = session.exec(select(Capsule).where(Capsule.date == today_str)).first()
    capsule_obj: Dict[str, Any]
    if cap:
        try:
            capsule_obj = {"date": cap.date, "items": json.loads(cap.items_json)}
        except Exception:
            capsule_obj = {"date": cap.date, "items": []}
    else:
        capsule_obj = {"date": today_str, "items": []}

    # Try LLM-based first, fallback to rule-based mapping-driven MCQs
    questions = _generate_questions_with_llm(capsule_obj)
    if not questions:
        all_topics: List[Dict[str, str]] = [
            {"paper": t.paper, "topic": t.topic} for t in (session.exec(select(SyllabusTopic)).all() or [])
        ]
        questions = _build_questions_from_capsule(capsule_obj, all_topics)
    payload = {"date": today_str, "name": _default_quiz_name(), "questions": questions}
    record = GeneratedTest(date=today_str, name=payload["name"], questions_json=json.dumps(questions))
    session.add(record)
    session.commit()
    session.refresh(record)
    return payload


def record_test_result(session: Session, user_id: int, test_name: str, answers: List[int]) -> Dict[str, Any]:
    today_str = date.today().isoformat()
    test = session.exec(
        select(GeneratedTest).where(GeneratedTest.date == today_str, GeneratedTest.name == test_name)
    ).first()
    if not test:
        return {"success": False, "detail": "Test not found"}
    try:
        questions = json.loads(test.questions_json)
    except Exception:
        questions = []
    total = len(questions)
    correct = 0
    review: List[Dict[str, Any]] = []
    for i, q in enumerate(questions):
        ai = int(q.get("answer_index", 0))
        chosen = answers[i] if i < len(answers) else -1
        ok = (chosen == ai)
        if ok:
            correct += 1
        review.append({
            "index": i,
            "chosen": chosen,
            "correct": ai,
            "ok": ok,
            "explanation": q.get("explanation"),
            "source": q.get("source"),
            "question": q.get("q"),
            "options": q.get("options", []),
        })
    score = round((correct / max(1, total)) * 100, 2)
    tr = TestResult(user_id=user_id, test_name=test_name, score=score, date=today_str)
    session.add(tr)
    session.commit()
    return {"success": True, "score": score, "total": total, "correct": correct, "review": review}


def get_progress_summary(session: Session, user_id: int) -> Dict[str, Any]:
    tests = session.exec(select(TestResult).where(TestResult.user_id == user_id)).all() or []
    if not tests:
        return {"tests": 0, "average": 0.0}
    avg = sum(t.score for t in tests) / len(tests)
    return {"tests": len(tests), "average": round(avg, 2)}


def get_test_history(session: Session, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    rows = session.exec(select(TestResult).where(TestResult.user_id == user_id)).all() or []
    rows = rows[-limit:]
    return [
        {"date": r.date, "score": r.score, "test_name": r.test_name}
        for r in rows
    ]
