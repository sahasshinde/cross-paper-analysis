"""Finds the 7 research aspects in one paper WITHOUT relying on headings.
Every sentence gets a score for every aspect; the best-scoring sentences
are returned with their page numbers."""
import math
import re
from pathlib import Path
from functools import lru_cache
import numpy as np

from app.services.pdf_service import extract_pages
from app.services.text_service import build_sentences
from app.services.evidence_service import normalise_pages
from app.services.embedding_service import embed
from app.services import aspect_config as cfg


@lru_cache(maxsize=1)
def _prototype_vectors():
    return {a: embed(cfg.PROTOTYPES[a]) for a in cfg.ASPECTS}


CITATION = re.compile(r"\[\d+(?:\s*[,\u2013-]\s*\d+)*\]|et al\.")


def _cue_score(text, aspect):
    """0..1. More telltale phrases -> closer to 1 (diminishing returns)."""
    total = sum(w for pattern, w in cfg.COMPILED_CUES[aspect] if pattern.search(text))
    return 1 - math.exp(-total)


def _position_score(pos, heading, aspect):
    lo, hi = cfg.POSITION[aspect]
    score = 1.0 if lo <= pos <= hi else 0.35
    if heading in cfg.HEADING_HINTS[aspect]:   # small bonus, never required
        score = min(1.0, score + 0.5)
    return score


def score_sentences(sentences):
    """Adds s["scores"] = {aspect: 0..1} to every sentence."""
    vecs = embed([s["text"] for s in sentences])
    protos = _prototype_vectors()
    w = cfg.WEIGHTS
    for s in sentences:
        s["scores"] = {}
    for a in cfg.ASPECTS:
        sims = (vecs @ protos[a].T).max(axis=1)           # best match to examples
        emb = np.clip((sims - 0.3) / 0.5, 0, 1)           # rescale to 0..1
        for i, s in enumerate(sentences):
            cue = _cue_score(s["text"], a)
            total = (w["embedding"] * emb[i] + w["cue"] * cue
                     + w["position"] * _position_score(s["pos"], s["heading"], a))
            if a in cfg.GAP_ASPECTS:
                if cue < cfg.GAP_MIN_CUE:                 # needs a real telltale phrase
                    total = 0.0
                if s["heading"] in cfg.RELATED_HEADINGS:  # probably about other papers
                    total *= cfg.RELATED_PENALTY
                if CITATION.search(s["text"]):            # cites another study
                    total *= cfg.CITATION_PENALTY
                if cfg.GAP_NEGATIVE.search(s["text"]):    # closing remark, not a gap
                    total *= cfg.GAP_NEGATIVE_PENALTY
                if cfg.GAP_FILLER.search(s["text"]):      # "every study has limitations"
                    total = 0.0
            elif a in ("results", "methodology", "dataset"):
                if s["heading"] in cfg.RELATED_HEADINGS:  # other people's work
                    total *= 0.6
                if CITATION.search(s["text"]):
                    total *= 0.7
            elif a == "problem" and s["heading"] in ("related work", "related works", "literature review"):
                total *= 0.6
            s["scores"][a] = round(float(total), 3)


def _gap_kind(s):
    """'limitations' / 'future_work' if the sentence qualifies, else None.
    If it qualifies as both, the stronger label wins."""
    hits = [a for a in cfg.GAP_ASPECTS if s["scores"][a] >= cfg.THRESHOLD[a]]
    return max(hits, key=lambda a: s["scores"][a]) if hits else None


def _item(s, aspect):
    return {"text": s["text"], "page": s["page"],
            "heading": s["heading"], "score": s["scores"][aspect]}


def pick_aspects(sentences, top_k=None):
    top_k = top_k or cfg.TOP_K
    picked = {a: [] for a in cfg.ASPECTS}
    used = set()

    # 1) Limitations / future work: threshold-based
    #    (a paper may genuinely have none).
    for i, s in enumerate(sentences):
        kind = _gap_kind(s)
        if kind:
            picked[kind].append(_item(s, kind))
            used.add(i)

    # 2) Other aspects: every paper has them, so always show the best ones.
    #    Pass A: a sentence goes to the aspect where it scores highest.
    floor = cfg.MIN_DESCRIPTIVE_SCORE
    free = [i for i in range(len(sentences)) if i not in used]
    for a in cfg.DESCRIPTIVE:
        mine = [i for i in free
                if max(cfg.DESCRIPTIVE, key=lambda b: sentences[i]["scores"][b]) == a
                and sentences[i]["scores"][a] >= floor]
        mine.sort(key=lambda i: sentences[i]["scores"][a], reverse=True)
        for i in mine[:top_k[a]]:
            picked[a].append(_item(sentences[i], a))
            used.add(i)
    #    Pass B: aspects still short of top_k take their next-best unused
    #    sentence, taking turns so no aspect gets starved.
    for _ in range(max(top_k[a] for a in cfg.DESCRIPTIVE)):
        for a in cfg.DESCRIPTIVE:
            if len(picked[a]) >= top_k[a]:
                continue
            left = [i for i in range(len(sentences))
                    if i not in used and sentences[i]["scores"][a] >= floor]
            if left:
                i = max(left, key=lambda i: sentences[i]["scores"][a])
                picked[a].append(_item(sentences[i], a))
                used.add(i)

    for a in cfg.ASPECTS:
        picked[a].sort(key=lambda x: x["score"], reverse=True)
        picked[a] = picked[a][:top_k[a]]
    return picked


# ---- Dataset key facts: source, size, split, imbalance, missing values --------
# Pulled straight from the paper's own sentences (with page numbers), so the
# Dataset comparison can say "Kaggle, 6582 rows" vs "Veracity Trust Network,
# 73,303 records" even when the two papers use completely different data.
_DATASET_HEADINGS = {"dataset", "datasets", "dataset description", "data collection",
                     "materials and methods", "experimental setup", "methodology",
                     "method", "methods", "proposed method", "approach"}
_KNOWN_SOURCES = re.compile(r"\b(Kaggle|UCI(?: Machine Learning Repository)?|ImageNet|MNIST|"
                            r"CIFAR-?\d*|COCO|PlantVillage|TalkingData)\b")
_PROVIDED_BY = re.compile(r"\b[Pp]rovided by\s+((?:[A-Z][\w&\-]*\s*){1,6})")
_ROWS_COLS = re.compile(r"(\d[\d,]*)\s*rows\s*[\u00d7xX]\s*(\d+)\s*columns")
_COUNT = re.compile(r"\b(\d[\d,]{2,})\s+(records|images|samples|instances|documents|patients|"
                    r"examples|sentences|articles|papers|clicks|observations)\b")
_SPLIT = re.compile(r"(\d{1,2})%.{0,40}\btrain\w*.{0,40}?(\d{1,2})%.{0,25}\btest", re.I)
_KFOLD = re.compile(r"\b(ten|five|10|5)[- ]fold cross[- ]validation", re.I)
_SAMPLING = re.compile(r"\b((?:random )?(?:under|over)-?sampling|SMOTE|RUSBoost)\b", re.I)
_SKEWED = re.compile(r"\b(skewed|imbalanc\w+)\b", re.I)
_MISSING = re.compile(r"\b(MissForest|imputation|imput\w+|missing (?:values|data))\b", re.I)


def extract_dataset_facts(sentences):
    """[{label, value, page, text}] - first reliable mention per label.
    Sentences from Related Work or about other authors ("et al.") are skipped."""
    found = {}                                   # label -> (priority, fact)

    def put(label, value, s, priority=1):
        if label not in found or priority > found[label][0]:
            found[label] = (priority, {"label": label, "value": value,
                                       "page": s["page"], "text": s["text"]})

    for s in sentences:
        text = s["text"]
        if s["heading"] in cfg.RELATED_HEADINGS or "et al." in text:
            continue
        about_data = bool(re.search(r"\bdata ?sets?\b|\bdata\b", text, re.I)) \
                     or s["heading"] in _DATASET_HEADINGS
        if about_data:
            m = _KNOWN_SOURCES.search(text)
            if m:
                put("Source", m.group(1), s, 2)
            else:
                m = _PROVIDED_BY.search(text)
                if m:
                    put("Source", m.group(1).strip(), s, 1)
            m = _ROWS_COLS.search(text)
            if m:
                put("Size", f"{m.group(1)} rows \u00d7 {m.group(2)} columns", s, 2)
            elif re.search(r"data ?set|consist|contain|collected", text, re.I):
                m = _COUNT.search(text)
                if m:
                    put("Size", f"{m.group(1)} {m.group(2)}", s, 1)
        m = _SPLIT.search(text)
        if m:
            put("Split / validation", f"{m.group(1)}% train / {m.group(2)}% test", s, 2)
        else:
            m = _KFOLD.search(text)
            if m:
                k = {"ten": "10", "five": "5"}.get(m.group(1).lower(), m.group(1))
                put("Split / validation", f"{k}-fold cross-validation", s, 1)
        m = _SAMPLING.search(text)
        if m:
            put("Class imbalance", f"handled with {m.group(1).lower()}", s, 2)
        elif about_data and _SKEWED.search(text):
            put("Class imbalance", "noted (no handling technique stated)", s, 1)
        m = _MISSING.search(text)
        if m and about_data:
            v = "MissForest imputation" if m.group(1).lower() == "missforest" else m.group(1).lower()
            put("Missing values", v, s, 2 if "missforest" in text.lower() else 1)
    return [f for _, f in found.values()]


_CACHE = {}   # {(path, last-modified): result}  so each PDF is analysed once


def analyze_paper(pdf_path):
    key = (str(pdf_path), Path(pdf_path).stat().st_mtime)
    if key in _CACHE:
        return _CACHE[key]
    pages = extract_pages(pdf_path)
    sentences = build_sentences(pages)
    if not sentences:
        result = {"num_pages": len(pages), "num_sentences": 0,
                  "aspects": {a: [] for a in cfg.ASPECTS},
                  "pool": {a: [] for a in cfg.ASPECTS}, "dataset_facts": [],
                  "_pages": normalise_pages(pages),
                  "warning": "No readable text found (scanned PDF?)."}
    else:
        score_sentences(sentences)
        result = {"num_pages": len(pages), "num_sentences": len(sentences),
                  "aspects": pick_aspects(sentences),          # shown on screen
                  "pool": pick_aspects(sentences, cfg.COMPARE_TOP_K),  # used for comparison
                  "dataset_facts": extract_dataset_facts(sentences),
                  "_pages": normalise_pages(pages)}   # "_" = internal, never sent to browser
    _CACHE[key] = result
    return result
