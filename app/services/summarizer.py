from typing import Optional, List
import os
import re
import httpx


def _clean(text: str) -> str:
    text = " ".join((text or "").split())
    # normalize bullets
    text = text.replace("•", "-")
    return text.strip()


def _to_bullets(text: str, title: Optional[str] = None, min_points: int = 4, max_points: int = 8) -> str:
    """Normalize arbitrary text into hyphen bullets with short, complete lines.
    Ensures duplicates removed and each bullet ends with a period."""
    t = (text or "").strip()
    # Split on newlines first, then on sentence boundaries if needed
    parts = [p.strip(" -\t•") for p in t.splitlines() if p.strip()]
    if len(parts) < min_points:
        # Fallback to sentence split
        parts = re.split(r"(?<=[.!?])\s+", t)
        parts = [p.strip(" -\t•") for p in parts if p and len(p.split()) > 3]
    # Deduplicate and clip
    seen = set()
    norm = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip()
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        # Trim overly long bullets
        if len(p) > 240:
            p = p[:237].rstrip() + "…"
        if p and p[-1] not in ".!?…":
            p += "."
        norm.append(p)
        if len(norm) >= max_points:
            break
    # Ensure minimum bullets by truncating sentences further if needed
    if len(norm) < min_points and parts:
        for p in parts:
            if p.lower() not in seen:
                q = p.strip()
                if q and q[-1] not in ".!?…":
                    q += "."
                norm.append(q)
                if len(norm) >= min_points:
                    break
    head = f"{title.strip()} — Key Points" if title else None
    body = "\n".join([f"- {p}" for p in norm]) if norm else "- (No key points extracted.)"
    return f"{head}\n{body}" if head else body


def _textrank(text: str, max_sentences: int = 7) -> str:
    try:
        from sumy.parsers.plaintext import PlaintextParser  # type: ignore
        from sumy.nlp.tokenizers import Tokenizer  # type: ignore
        from sumy.summarizers.text_rank import TextRankSummarizer  # type: ignore
        parser = PlaintextParser.from_string(text or "", Tokenizer("english"))
        summarizer = TextRankSummarizer()
        sentences = summarizer(parser.document, max_sentences)
        out = " ".join(str(s) for s in sentences)
        out = _clean(out)
        if out and len(out.split()) > 15:
            return out
    except Exception:
        pass
    # Fallback: compact lead
    parts = [p.strip() for p in (text or "").replace("\n", " ").split(".") if p.strip()]
    lead = ". ".join(parts[: max(3, min(max_sentences, len(parts)))])
    if lead and not lead.endswith("."):
        lead += "."
    return lead


def _hf_generate(prompt: str, model_url: Optional[str] = None, max_new_tokens: int = 320) -> Optional[str]:
    # Default to a summarization-specialized model
    url = model_url or os.getenv(
        "HF_SUMMARY_MODEL_URL",
        "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
    )
    headers = {"Content-Type": "application/json"}
    token = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": max_new_tokens}})
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    txt = data[0].get("generated_text") or data[0].get("summary_text")
                    return _clean(txt or "")
                if isinstance(data, dict) and "generated_text" in data:
                    return _clean(str(data["generated_text"]))
    except Exception:
        return None
    return None


def summarize_text(text: str, max_sentences: int = 7) -> str:
    """Summarize using env-selected backend: hf | textrank (default)."""
    backend = os.getenv("SUMMARIZER_BACKEND", "textrank").lower()
    text = text or ""
    if backend == "hf":
        # Generic LLM summary prompt – enforce bullets and complete sentences
        prompt = (
            "You are a precise news summarizer. Produce a short title and 5-8 crisp bullet points.\n"
            "Rules: Each bullet must be a complete fact-based sentence, end with a period, avoid redundancy, include dates/numbers/names.\n"
            "Format strictly as: <Short Title> — Key Points\n- Bullet 1\n- Bullet 2\n...\n\n"
            f"Article (cleaned):\n{text[:6000]}"
        )
        resp = _hf_generate(prompt)
        if resp:
            return _to_bullets(resp, None)
        # Fallback to textrank if HF fails
        return _textrank(text, max_sentences=max_sentences)
    # Default: TextRank
    return _textrank(text, max_sentences=max_sentences)


def summarize_news_article(title: str, text: str, url: Optional[str] = None) -> str:
    """News-specific summary in the requested format (title + key points)."""
    backend = os.getenv("SUMMARIZER_BACKEND", "textrank").lower()
    if backend == "hf":
        prompt = (
            f"Title: {title}\nURL: {url or ''}\n\n"
            "Summarize into 5-8 concise bullets with a short title.\n"
            "Strict format: <Short Title> — Key Points followed by hyphen bullets.\n"
            "Each bullet must be a complete, fact-based sentence ending with a period. Avoid repetition.\n\n"
            f"Article:\n{text[:6000]}"
        )
        resp = _hf_generate(prompt, max_new_tokens=360)
        if resp:
            return _to_bullets(resp, None)
    # Fallback: TextRank → bulletize
    body = _textrank(text, max_sentences=8)
    return _to_bullets(body, title)


def summarize_many(items: List[str], max_sentences: int = 7) -> List[str]:
    return [summarize_text(t, max_sentences=max_sentences) for t in items]
