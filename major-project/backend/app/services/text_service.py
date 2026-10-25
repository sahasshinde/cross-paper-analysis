"""Turns raw page text into clean sentences, each tagged with page number,
the most recent heading seen (a WEAK hint only) and relative position."""
import re
from collections import Counter

# Headings are only used as a soft hint, plus to cut off the References list.
KNOWN_HEADINGS = {
    "abstract", "introduction", "background", "related work", "related works",
    "literature review", "method", "methods", "methodology", "materials and methods",
    "proposed method", "proposed methodology", "approach", "experiments",
    "experimental setup", "experimental results", "experiments and results",
    "implementation details", "dataset", "datasets", "dataset description",
    "data collection", "results", "results and discussion", "discussion",
    "discussion and conclusion", "conclusion", "conclusions",
    "conclusion and future work", "limitations", "limitations and future work",
    "future work", "future directions", "future research", "references",
    "acknowledgements", "acknowledgments", "objectives", "contributions",
}

# Front-matter / paper-outline sentences that are never research content.
BOILERPLATE = re.compile(
    r"authors.? contributions|corresponding author|article no\.|open access|"
    r"creative commons|licensed under|all rights reserved|competing interests?|"
    r"carried out in collaboration|peer.review|"
    r"read and approved|\bmanuscript\b|institute of science|\buniversity\b|department of|college of|"
    r"\b(presented|discussed|outlined|summari[sz]ed|given|described|organi[sz]ed|appears?) in section\b|"
    r"\bsection [ivx\d]+\b.{0,30}\b(presents?|offers?|concludes?|outlines?|summari[sz]es?)|"
    r"remainder of (this|the) (paper|document|article)", re.I)

ABBREVIATIONS = ["et al.", "e.g.", "i.e.", "Fig.", "Figs.", "Eq.", "Eqs.",
                 "vs.", "No.", "Sec.", "Tab.", "approx.", "cf.", "etc."]


def heading_of(line):
    """Returns a normalised heading name if the line looks like one, else None."""
    line = line.strip()
    if not line or len(line) > 60 or line.endswith("."):
        return None
    # strip numbering such as "1.", "2.3", "IV."
    line = re.sub(r"^(\d+(\.\d+)*\.?|[IVXivx]+\.)\s+", "", line)
    name = re.sub(r"[^a-z ]", "", line.lower()).strip()
    return name if name in KNOWN_HEADINGS else None


def is_caption_line(line):
    """'TABLE 9. ...' / 'Fig. 2. ...' lines are never real sentences."""
    return bool(re.match(r"^\s*(TABLE|FIGURE|FIG\.|Table|Figure|Fig\.)\s*[\dIVXivx]+", line))


def generic_heading(line):
    """ALL-CAPS lines such as 'IX. COMPARISON WITH PREVIOUS STUDIES' or
    'A. DATASET DESCRIPTION' are headings even if we do not know the name."""
    s = line.strip()
    if not s or len(s) > 70 or s.endswith((".", ",", ";", ":")):
        return None
    m = re.match(r"^(\d+(\.\d+)*\.?|[IVXLC]+\.|[A-Z]\.)\s+(.*)$", s)
    body = m.group(3) if m else s
    if m and re.match(r"^\d+\.\d+", m.group(1)) and len(body.split()) <= 6 and body[:1].isupper():
        return re.sub(r"[^a-z ]", "", body.lower()).strip()   # "4.2 Data Preprocessing"
    if any(c.isdigit() for c in body):          # page footers like "VOLUME 13, 2025"
        return None
    if sum(c.isalpha() for c in body) >= 4 and body.isupper() and len(body.split()) >= 2:
        return re.sub(r"[^a-z ]", "", body.lower()).strip()
    return None


def _join_lines(lines):
    """Joins PDF lines into one paragraph and repairs 'exam-\\nple' breaks."""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out.endswith("-") and ln[:1].islower():
            out = out[:-1] + ln
        else:
            out += (" " if out else "") + ln
    return out


def split_sentences(text):
    for ab in ABBREVIATIONS:                       # protect "et al." etc.
        text = text.replace(ab, ab.replace(".", "<DOT>"))
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9\(\["\u201c])', text)
    return [p.replace("<DOT>", ".").strip() for p in parts]


# "ABSTRACT In online advertising..." / "COMPARISON WITH PREVIOUS STUDIES A comparison..."
# -> a heading got glued to the sentence; cut the ALL-CAPS run off the front.
_CAPS_RUN = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s+)?((?:[A-Z]{2,} ){1,8})(?=[A-Z])")


def clean_sentence(s):
    m = _CAPS_RUN.match(s)
    if m and len(m.group(1)) >= 8:
        s = s[m.end():]
    return s.strip()


def _is_good_sentence(s):
    if not 40 <= len(s) <= 500:
        return False
    if len(s.split()) < 7:
        return False
    letters = sum(c.isalpha() for c in s)
    digits = sum(c.isdigit() for c in s)
    if letters / len(s) < 0.6 or digits / len(s) > 0.3:   # tables, formulas
        return False
    if "http" in s or "@" in s:
        return False
    if re.match(r"^(Figure|Fig\.|Table)\s", s):            # captions
        return False
    if BOILERPLATE.search(s):
        return False
    if re.match(r"^\d{1,2}\s+[A-Z]", s) and s.count("%") >= 2:   # table rows
        return False
    return True


def build_sentences(pages):
    """pages: [{"page": 1, "text": "..."}]  ->  [{"text","page","heading","pos"}]
    Everything after the References heading is dropped."""
    items, heading, in_refs = [], None, False

    for p in pages:
        buffer = []

        def flush():
            para = _join_lines(buffer)
            buffer.clear()
            for s in split_sentences(para):
                s = clean_sentence(s)
                if _is_good_sentence(s):
                    items.append({"text": s, "page": p["page"], "heading": heading})

        for line in p["text"].split("\n"):
            if is_caption_line(line):
                flush()
                continue
            h = heading_of(line)
            if h:
                flush()
                heading = h
                if h == "references":
                    in_refs = True
                    break
                continue
            g = generic_heading(line)
            if g:
                flush()
                heading = g
                continue
            buffer.append(line)
        if in_refs:
            break
        flush()

    # drop running headers/footers: same sentence on 3+ pages
    counts = Counter(i["text"] for i in items)
    items = [i for i in items if counts[i["text"]] < 3]

    n = len(items)
    for k, it in enumerate(items):
        it["pos"] = k / (n - 1) if n > 1 else 0.0
    return items
