"""Stage 3: compares papers LIKE WITH LIKE, aspect by aspect.

Dataset statements are only compared with dataset statements, limitations
with limitations, and so on. Embeddings put sentences with similar MEANING
close together; cosine similarity measures that closeness
(1 = same meaning, 0 = unrelated).

Rules that keep the output clean and honest:
 * Only statements from DIFFERENT papers are paired.
 * ONE-TO-ONE matching: for every two papers, each statement is used in at
   most one pair (its best available partner). No statement is repeated.
 * Papers on one topic share many words, so every pair scores fairly high.
   We therefore report a per-aspect BASELINE (average similarity of all
   pairs) and start the slider at baseline + margin."""
import numpy as np
from app.config import EMBEDDING_MODEL
from app.services.embedding_service import embed
from app.services import aspect_config as cfg


def _view(it):
    return {"paper": it["paper"], "page": it["page"], "text": it["text"]}


def _match_one_to_one(sim, min_sim):
    """sim: (n, m) matrix. Greedy best-first matching, each row/col used once."""
    cands = sorted(((sim[i][j], i, j) for i in range(sim.shape[0])
                    for j in range(sim.shape[1]) if sim[i][j] >= min_sim), reverse=True)
    used_i, used_j, out = set(), set(), []
    for s, i, j in cands:
        if i in used_i or j in used_j:
            continue
        used_i.add(i); used_j.add(j); out.append((float(s), i, j))
    return out


def compare_aspects(papers):
    """papers: [{"name": str, "pool": {aspect: [{"text","page",...}]}}]"""
    texts, owner = [], []                        # every statement, embedded once
    for pi, p in enumerate(papers):
        for aspect in cfg.ASPECTS:
            for st in p["pool"].get(aspect, []):
                texts.append(st["text"]); owner.append((pi, aspect, st))
    vecs = embed(texts) if texts else np.zeros((0, 1))

    result = {"model": EMBEDDING_MODEL, "papers": [p["name"] for p in papers],
              "dataset_facts": [{"name": p["name"], "facts": p.get("facts", [])} for p in papers],
              "aspects": {}}
    for aspect in cfg.ASPECTS:
        # statement indices of this aspect, grouped by paper
        by_paper = {pi: [k for k, (q, a, _) in enumerate(owner) if q == pi and a == aspect]
                    for pi in range(len(papers))}
        counts = [{"name": p["name"], "n": len(by_paper[pi])} for pi, p in enumerate(papers)]
        pairs, all_sims = [], []
        for pa in range(len(papers)):
            for pb in range(pa + 1, len(papers)):
                ia, ib = by_paper[pa], by_paper[pb]
                if not ia or not ib:
                    continue
                sim = vecs[ia] @ vecs[ib].T
                all_sims.extend(sim.flatten().tolist())
                for s, x, y in _match_one_to_one(sim, cfg.MIN_PAIR_SIMILARITY):
                    pairs.append({
                        "similarity": round(s, 3),
                        "a": _view({"paper": papers[pa]["name"], **owner[ia[x]][2]}),
                        "b": _view({"paper": papers[pb]["name"], **owner[ib[y]][2]})})
        pairs.sort(key=lambda p: p["similarity"], reverse=True)
        baseline = float(np.mean(all_sims)) if all_sims else None
        default = cfg.DEFAULT_THRESHOLD_MIN if baseline is None else min(
            0.85, max(cfg.DEFAULT_THRESHOLD_MIN, baseline + cfg.DEFAULT_THRESHOLD_MARGIN))
        statements = [{"paper": papers[owner[k][0]]["name"], "page": owner[k][2]["page"],
                       "text": owner[k][2]["text"]}
                      for pi in range(len(papers)) for k in by_paper[pi]]
        result["aspects"][aspect] = {
            "counts": counts,
            "statements": statements,          # everything that was compared (for checking)
            "baseline": None if baseline is None else round(baseline, 3),
            "default_threshold": round(default, 2),
            "pairs": pairs[:cfg.MAX_PAIRS],
        }
    return result
