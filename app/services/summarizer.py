from typing import List


def simple_summarize(text: str, max_sentences: int = 3) -> str:
    parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
    return ". ".join(parts[:max_sentences]) + ("." if parts else "")


def summarize_many(items: List[str]) -> List[str]:
    return [simple_summarize(t) for t in items]

