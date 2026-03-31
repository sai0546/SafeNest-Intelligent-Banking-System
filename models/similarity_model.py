from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

_vectorizer = None
_matrix = None
_documents = None


def _build_model(documents: list):
    global _vectorizer, _matrix, _documents
    _vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )
    _matrix = _vectorizer.fit_transform(documents)
    _documents = documents


def find_best_match(query: str, documents: list) -> tuple:
    """
    Returns (best_index, similarity_score).
    Score is between 0.0 (no match) and 1.0 (perfect match).
    """
    global _vectorizer, _matrix, _documents

    # Rebuild if documents changed
    if _vectorizer is None or _documents != documents:
        _build_model(documents)

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _matrix).flatten()
    best_idx = int(np.argmax(scores))
    return best_idx, float(scores[best_idx])
