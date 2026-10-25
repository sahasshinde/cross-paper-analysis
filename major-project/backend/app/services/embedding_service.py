"""Turns text into vectors. The rest of the project only calls embed(),
so swapping in SciBERT / SPECTER2 later means changing this file only."""
from functools import lru_cache
import numpy as np
from app.config import EMBEDDING_MODEL

_CACHE = {}   # text -> vector, so the same sentence is never embedded twice


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer  # slow import, so lazy
    return SentenceTransformer(EMBEDDING_MODEL)  # downloads once, then cached


def embed(texts):
    """list[str] -> numpy array (n, dim). Vectors are length-1, so
    dot product == cosine similarity."""
    missing = [t for t in dict.fromkeys(texts) if t not in _CACHE]
    if missing:
        vecs = _load_model().encode(missing, batch_size=32, normalize_embeddings=True,
                                    show_progress_bar=False)
        for t, v in zip(missing, vecs):
            _CACHE[t] = v
    return np.array([_CACHE[t] for t in texts])
