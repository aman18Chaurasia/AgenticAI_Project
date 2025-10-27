import json
import logging
from datetime import date, timedelta
from collections import Counter
from sqlmodel import Session, select
from ..models.user import StudyPlan, User, TestResult
from ..models.content import SyllabusTopic, Capsule

logger = logging.getLogger(__name__)


def _even_chunks(items, weeks: int) -> list[list[str]]:
    chunks: list[list[str]] = [[] for _ in range(max(1, weeks))]
    for i, it in enumerate(items):
        chunks[i % len(chunks)].append(it)
    return chunks


def _default_hours(user: User) -> int:
    return 10


def generate_plan_for_default_user(session: Session) -> None:
    user = session.exec(select(User)).first()
    if not user:
        user = User(email="student@example.com", full_name="Student", hashed_password="", role="student")
        session.add(user)
        session.commit()
        session.refresh(user)
    topics = session.exec(select(SyllabusTopic)).all()
    topic_names = [t.topic for t in topics]
    weeks = 8
    hours = _default_hours(user)
    buckets = _even_chunks(topic_names, weeks)
    plan = {"generated_on": str(date.today()), "weeks": []}
    for w_i in range(weeks):
        plan["weeks"].append({"week": w_i + 1, "hours": hours, "tasks": buckets[w_i] + (["Weekly revision"] if w_i % 2 == 0 else [])})
    existing = session.exec(select(StudyPlan).where(StudyPlan.user_id == (user.id or 0))).first()
    if existing:
        existing.plan_json = json.dumps(plan)
        session.add(existing)
    else:
        session.add(StudyPlan(user_id=user.id or 0, target_year=date.today().year, available_hours_per_week=10, plan_json=json.dumps(plan)))
    session.commit()


def generate_plan_for_user(session: Session, user_id: int) -> StudyPlan:
    """Generate a baseline multi-week study plan for a specific user.

    Uses the syllabus topics to distribute tasks evenly across weeks and
    sets a reasonable default for available hours.
    """
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    topics = session.exec(select(SyllabusTopic)).all()
    topic_names = [t.topic for t in topics]
    # Boost prioritization using recent capsule trends
    weights = _topic_trend_weights(session, days=14)
    topic_names = _prioritize_topics(topic_names, weights)
    weeks = 8
    hours = _default_hours(user)
    buckets = _even_chunks(topic_names, weeks)
    plan = {"generated_on": str(date.today()), "weeks": []}
    for w_i in range(weeks):
        plan["weeks"].append(
            {
                "week": w_i + 1,
                "hours": hours,
                "tasks": buckets[w_i] + (["Weekly revision"] if w_i % 2 == 0 else []),
            }
        )
    existing = session.exec(select(StudyPlan).where(StudyPlan.user_id == user.id)).first()
    if existing:
        existing.plan_json = json.dumps(plan)
        session.add(existing)
        session.commit()
        return existing
    sp = StudyPlan(
        user_id=user.id,
        target_year=date.today().year,
        available_hours_per_week=hours,
        plan_json=json.dumps(plan),
    )
    session.add(sp)
    session.commit()
    session.refresh(sp)
    return sp


def _topic_trend_weights(session: Session, days: int = 14) -> dict[str, float]:
    """Compute simple frequency-based weights from recent capsules."""
    try:
        end = date.today()
        start = end - timedelta(days=days)
        caps = session.exec(
            select(Capsule).where(Capsule.date >= str(start), Capsule.date <= str(end))
        ).all() or []
        counts: Counter[str] = Counter()
        for c in caps:
            try:
                items = json.loads(c.items_json) or []
            except Exception:
                items = []
            for it in items:
                for tp in it.get("topics", []) or []:
                    name = str(tp.get("topic") or "").strip()
                    if name:
                        counts[name] += 1
        if not counts:
            return {}
        maxc = max(counts.values())
        return {k: 1.0 + (v / maxc) for k, v in counts.items()}  # 1.0..2.0
    except Exception as exc:
        logger.debug("trend weights error: %s", exc)
        return {}


def _prioritize_topics(names: list[str], weights: dict[str, float]) -> list[str]:
    if not weights:
        return names
    return sorted(names, key=lambda n: weights.get(n, 1.0), reverse=True)


def _infer_weak_topics(test_name: str, syllabus: list[SyllabusTopic]) -> list[str]:
    n = (test_name or "").lower()
    matched: list[str] = []
    for t in syllabus:
        k = (t.topic or "").lower()
        if not k:
            continue
        # simple substring match
        if k in n:
            matched.append(t.topic)
        else:
            # split keywords field
            kws = (t.keywords or "").lower().split(",")
            if any(kw.strip() and kw.strip() in n for kw in kws):
                matched.append(t.topic)
    return matched


def adapt_plan_with_feedback(session: Session, user_id: int) -> None:
    tests = session.exec(select(TestResult).where(TestResult.user_id == user_id)).all()
    if not tests:
        return
    avg = sum(t.score for t in tests) / max(1, len(tests))
    plan = session.exec(select(StudyPlan).where(StudyPlan.user_id == user_id)).first()
    if plan:
        obj = json.loads(plan.plan_json)
        # Hours scaling based on average score
        for w in obj.get("weeks", []):
            base = int(w.get("hours", 10))
            if avg >= 75:
                w["hours"] = max(6, int(base * 0.9))
            elif avg <= 60:
                w["hours"] = min(18, int(base * 1.2))
            else:
                w["hours"] = base
        # Weak-topic targeting based on recent tests names
        syllabus = session.exec(select(SyllabusTopic)).all()
        counts: Counter[str] = Counter()
        for t in tests[-8:]:
            for topic in _infer_weak_topics(t.test_name or "", syllabus):
                weight = 1.5 if t.score < 50 else (1.0 if t.score < 70 else 0.5)
                counts[topic] += weight
        weak = [tp for tp, _ in counts.most_common(8)]
        # Also bring in current trends from recent capsules
        trend_weights = _topic_trend_weights(session, days=14)
        # Reorder each week's tasks to prioritize weak + trending topics first
        for w in obj.get("weeks", []):
            tasks = w.get("tasks", [])
            # Inject targeted revision tasks early
            inject = [f"Revise: {x}" for x in weak[:2] if f"Revise: {x}" not in tasks]
            # Add weekly CA practice anchor
            trending = sorted(trend_weights.items(), key=lambda kv: kv[1], reverse=True)
            ca_targets = [t for t, _ in trending[:2]]
            ca_tasks = [f"Current Affairs: {x}" for x in ca_targets if f"Current Affairs: {x}" not in tasks]
            # Deduplicate and reorder by priority (weak/trend first)
            def _priority(tn: str) -> float:
                base = 0.0
                name = tn.replace("Revise: ", "").replace("Current Affairs: ", "")
                if name in weak:
                    base += 2.0
                base += trend_weights.get(name, 0)
                return -base  # lower is earlier

            merged = list(dict.fromkeys(inject + ca_tasks + tasks))
            # keep revision/current affairs labels together; others sorted by topic priority
            merged_sorted = merged[:]
            try:
                merged_sorted.sort(key=_priority)
            except Exception:
                pass
            w["tasks"] = merged_sorted
        obj["feedback_summary"] = {
            "tests_considered": len(tests),
            "average_score": round(avg, 2),
            "weak_topics": weak,
        }
        plan.plan_json = json.dumps(obj)
        session.add(plan)
        session.commit()
