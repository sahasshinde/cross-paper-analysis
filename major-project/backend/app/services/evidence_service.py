"""Stage 5: evidence verification. A gap is only shown with proof that
 (1) every quoted passage really exists on the cited page of the PDF,
 (2) the gap wording is semantically supported by its evidence, and
 (3) the wording contains no numbers that the evidence does not contain."""
import re
import numpy as np
from app.services.embedding_service import embed


def _norm(text):
    """lower-case letters + digits only, so line breaks, hyphens and spacing
    differences in the PDF cannot hide a genuine match."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def normalise_pages(pages):
    """[{"page": 1, "text": "..."}] -> {1: "normalisedtext"}"""
    return {p["page"]: _norm(p["text"]) for p in pages}


def verify_evidence(statements, pages_by_paper):
    """Adds "verified": True/False to each evidence statement."""
    out = []
    for s in statements:
        page_text = pages_by_paper.get(s["paper"], {}).get(s["page"], "")
        n = _norm(s["text"])
        out.append({**s, "verified": bool(n) and n in page_text})
    return out


def _numbers(text):
    return {m.replace(",", "") for m in re.findall(r"\d[\d,\.]*\d|\d", text)}


def numbers_supported(title, evidence):
    """True if every number in the gap wording appears in some evidence text."""
    allowed = set()
    for e in evidence:
        allowed |= _numbers(e["text"])
    return _numbers(title) <= allowed


def support_scores(title, evidence):
    """(mean, min) cosine similarity between the gap wording and each evidence statement."""
    vecs = embed([title] + [e["text"] for e in evidence])
    sims = vecs[1:] @ vecs[0]
    return float(np.mean(sims)), float(np.min(sims))
