"""Stage 4: groups limitation / future-work statements from ALL papers into
recurring issues.

How it works (explainable for the examiner):
 1. Pool every limitation and future-work statement, remembering paper + page.
 2. Embed each statement (same transformer model as Stage 3).
 3. Agglomerative clustering (scikit-learn): start with every statement alone,
    repeatedly merge the two closest groups (average linkage) until the groups
    are further apart than the chosen strictness.
 4. A group supported by at least 2 DIFFERENT papers is a RECURRING ISSUE.
    Groups from a single paper are kept separately.
 5. Evidence strength depends on how many of the uploaded papers support it."""
import math
import re
from collections import Counter

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from app.config import EMBEDDING_MODEL
from app.services.embedding_service import embed
from app.services import aspect_config as cfg

STOP = set("""this that with from have were been their there which while also than then them they
into more most such only both each other these those some what when where will would could should
can may might using used use based paper study work works future further however although
because between within across over under about after before during very much many""".split())


def evidence_strength(n, total):
    """High / Medium / Low from supporting papers n out of total uploaded."""
    ratio = n / total if total else 0
    if n >= cfg.STRENGTH_HIGH[0] and ratio >= cfg.STRENGTH_HIGH[1]:
        return "High"
    if n >= cfg.STRENGTH_MEDIUM[0] and ratio >= cfg.STRENGTH_MEDIUM[1]:
        return "Medium"
    return "Low"


def _tokens(text):
    return [w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP]


def _key_terms(group_texts, all_texts, k=5):
    """Words frequent in this group but rare in the other statements (TF-IDF)."""
    df = Counter()
    for t in all_texts:
        df.update(set(_tokens(t)))
    tf = Counter()
    for t in group_texts:
        tf.update(_tokens(t))
    n = len(all_texts)
    score = {w: c * (math.log((n + 1) / (df[w] + 1)) + 1) for w, c in tf.items()}
    return [w for w, _ in sorted(score.items(), key=lambda x: -x[1])[:k]]


def _agglomerate(dist, cut):
    try:
        model = AgglomerativeClustering(n_clusters=None, metric="precomputed",
                                        linkage="average", distance_threshold=cut)
    except TypeError:                            # older scikit-learn
        model = AgglomerativeClustering(n_clusters=None, affinity="precomputed",
                                        linkage="average", distance_threshold=cut)
    return model.fit_predict(dist)


def cluster_statements(papers, threshold=None):
    """papers: [{"name": str, "pool": {aspect: [{"text","page",...}]}}]"""
    names = [p["name"] for p in papers]
    items = []
    for pi, p in enumerate(papers):
        for kind in cfg.CLUSTER_ASPECTS:
            for st in p["pool"].get(kind, []):
                items.append({"paper": p["name"], "pi": pi, "kind": kind,
                              "text": st["text"], "page": st["page"]})
    out = {"model": EMBEDDING_MODEL, "total_papers": len(papers),
           "num_statements": len(items), "baseline": None, "threshold": None,
           "default_threshold": None, "recurring": [], "single_paper": []}
    if len(items) < 2:
        return out

    vecs = embed([it["text"] for it in items])
    sim = np.clip(vecs @ vecs.T, -1.0, 1.0)
    cross = [sim[i][j] for i in range(len(items)) for j in range(i + 1, len(items))
             if items[i]["pi"] != items[j]["pi"]]
    baseline = float(np.mean(cross)) if cross else None
    default = cfg.CLUSTER_MIN if baseline is None else min(
        cfg.CLUSTER_MAX, max(cfg.CLUSTER_MIN, baseline + cfg.CLUSTER_MARGIN))
    thr = default if threshold is None else min(0.95, max(0.3, float(threshold)))

    dist = np.clip(1.0 - sim, 0.0, None)
    np.fill_diagonal(dist, 0.0)
    labels = _agglomerate(dist, 1.0 - thr)

    all_texts = [it["text"] for it in items]
    groups = {}
    for idx, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(idx)

    clusters = []
    for members in groups.values():
        sub = sim[np.ix_(members, members)]
        if len(members) > 1:
            mean_to_others = (sub.sum(axis=1) - 1.0) / (len(members) - 1)
            rep = members[int(np.argmax(mean_to_others))]        # most central statement
            cohesion = float((sub.sum() - len(members)) / (len(members) * (len(members) - 1)))
        else:
            rep, cohesion = members[0], 1.0
        sup = sorted({items[m]["pi"] for m in members})
        ordered = sorted(members, key=lambda m: (items[m]["pi"], items[m]["page"]))
        view = lambda m: {"paper": items[m]["paper"], "page": items[m]["page"],
                          "kind": items[m]["kind"], "text": items[m]["text"]}
        clusters.append({
            "num_papers": len(sup),
            "papers": [names[i] for i in sup],
            "strength": evidence_strength(len(sup), len(papers)) if len(sup) >= 2 else None,
            "cohesion": round(cohesion, 3),
            "key_terms": _key_terms([items[m]["text"] for m in members], all_texts),
            "representative": view(rep),
            "statements": [view(m) for m in ordered],
            "kinds": dict(Counter(items[m]["kind"] for m in members)),
        })

    recurring = [c for c in clusters if c["num_papers"] >= 2]
    recurring.sort(key=lambda c: (-c["num_papers"], -c["cohesion"], -len(c["statements"])))
    single = sorted((c for c in clusters if c["num_papers"] < 2), key=lambda c: c["papers"][0])
    for i, c in enumerate(recurring, 1):
        c["id"] = i
    for i, c in enumerate(single, 1):
        c["id"] = i
    out.update({"baseline": None if baseline is None else round(baseline, 3),
                "threshold": round(thr, 2), "default_threshold": round(default, 2),
                "recurring": recurring, "single_paper": single})
    return out
