from typing import Optional
import re
import httpx


def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s


def fetch_html(url: str, timeout: float = 10.0) -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (CivicBriefs.ai)"}
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            r = client.get(url)
            if r.status_code == 200 and r.text:
                return r.text
    except Exception:
        return None
    return None


def extract_with_trafilatura(url: str, html: Optional[str]) -> Optional[str]:
    try:
        import trafilatura  # type: ignore
        text = None
        if html:
            text = trafilatura.extract(html, include_comments=False, include_tables=False)
        if not text:
            text = trafilatura.extract_url(url)
        if text:
            return _clean_text(text)
    except Exception:
        pass
    return None


def extract_article_text(url: str) -> Optional[str]:
    """Attempt to extract the main article text for a URL. Returns None on failure."""
    html = fetch_html(url)
    # Try robust extractor
    text = extract_with_trafilatura(url, html)
    if text and len(text) > 300:
        return text
    # Fallback: plain HTML text + meta description
    try:
        if html:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(html, "html.parser")
            # Try meta descriptions first
            md = None
            for sel in [
                "meta[name='description']",
                "meta[name='Description']",
                "meta[property='og:description']",
                "meta[name='twitter:description']",
            ]:
                tag = soup.select_one(sel)
                if tag and tag.get("content"):
                    md = _clean_text(tag["content"]) if not md else md
            if md and len(md) > 80:
                return md
            # Then full visible text
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            t = _clean_text(soup.get_text(" "))
            if t and len(t) > 180:
                return t
    except Exception:
        pass
    return None
