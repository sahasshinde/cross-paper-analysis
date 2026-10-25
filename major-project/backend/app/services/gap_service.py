"""Stage 5: turns each recurring issue into a POTENTIAL RESEARCH GAP.

The gap is derived only from the grouped statements (never from a bare
"find the research gap" prompt) and is shipped together with its evidence and
a verification report. Wording comes from a template by default (offline, no
model needed); a local LLM can be enabled, but its output is rejected when it
is not supported by the evidence."""
import re
from app.services import aspect_config as cfg
from app.services import llm_service
from app.services.evidence_service import verify_evidence, support_scores, numbers_supported

_LEAD = re.compile(r"^(however|moreover|additionally|furthermore|yet|thus|therefore|overall|"
                   r"in addition|as a result|in the future|nevertheless|also|but)\b[,\s]*", re.I)
_KIND = {"limitations": "limitation", "future_work": "future-work"}


def condense(text, max_chars=None):
    """Drops lead-in words ("However,") and trims to a readable length."""
    s = _LEAD.sub("", text.strip())
    s = s[:1].upper() + s[1:]

    if not s:
        return s

    return s[:1].upper() + s[1:]


def template_wording(cluster, total):
    title = condense(cluster["representative"]["text"])
    kinds = ", ".join(f"{n} {_KIND[k]}" for k, n in cluster["kinds"].items())
    terms = ", ".join(cluster["key_terms"][:5])
    expl = (f"Raised by {cluster['num_papers']} of {total} papers "
            f"({', '.join(cluster['papers'])}): {kinds} statement(s) describe a related "
            f"unresolved issue (shared terms: {terms}). This is a candidate gap derived from "
            "the uploaded papers; its novelty has not been checked against other literature.")
    return title, expl


def word_gap(cluster, total, evidence):
    """-> (title, explanation, method). Tries the optional LLM, falls back safely."""
    note = ""
    if llm_service.is_enabled():
        try:
            subset = evidence[:cfg.GAP_LLM_MAX_STATEMENTS]
            title, expl = llm_service.generate_gap(subset, cluster["num_papers"])
            mean, _ = support_scores(title, evidence)
            if numbers_supported(title, evidence) and mean >= cfg.GAP_SUPPORT_MIN:
                return title, expl, "local LLM"
            note = " (LLM wording rejected: not supported by the evidence)"
        except Exception:
            note = " (LLM unavailable)"
    title, expl = template_wording(cluster, total)
    return title, expl, "template" + note


def build_gaps(cluster_result, pages_by_paper):
    total = cluster_result["total_papers"]
    gaps = []
    for c in cluster_result["recurring"]:
        evidence = verify_evidence(c["statements"], pages_by_paper)
        title, expl, method = word_gap(c, total, evidence)
        mean, low = support_scores(title, evidence)
        found = sum(e["verified"] for e in evidence)
        ok = (found == len(evidence) and mean >= cfg.GAP_SUPPORT_MIN
              and numbers_supported(title, evidence))
        gaps.append({
            "id": c["id"], "title": title, "explanation": expl, "wording": method,
            "strength": c["strength"], "num_papers": c["num_papers"], "total_papers": total,
            "papers": c["papers"], "key_terms": c["key_terms"], "cohesion": c["cohesion"],
            "verification": {"quotes_verified": found, "quotes_total": len(evidence),
                             "support_mean": round(mean, 3), "support_min": round(low, 3),
                             "status": "Verified" if ok else "Check evidence"},
            "evidence": evidence,
        })
    return gaps
