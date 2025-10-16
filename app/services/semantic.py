from typing import List, Tuple


def tfidf_similarity(query: str, corpus: List[str]) -> List[Tuple[int, float]]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform([query] + corpus)
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        return sorted(list(enumerate(sims)), key=lambda x: x[1], reverse=True)
    except Exception:
        scores = []
        q = set(query.lower().split())
        for i, doc in enumerate(corpus):
            d = set(doc.lower().split())
            inter = len(q & d)
            denom = len(q) + len(d) - inter or 1
            scores.append((i, inter / denom))
        return sorted(scores, key=lambda x: x[1], reverse=True)

