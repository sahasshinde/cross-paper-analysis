import fitz  # PyMuPDF


def extract_pages(pdf_path):
    """Returns [{"page": 1, "text": "..."}, ...] so page numbers are kept."""
    doc = fitz.open(pdf_path)
    pages = [{"page": i, "text": _page_text(p)} for i, p in enumerate(doc, 1)]
    doc.close()
    return pages


def _page_text(page):
    # block = (x0, y0, x1, y1, text, block_no, type); type 0 = text
    blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    mid = page.rect.width / 2
    left = [b for b in blocks if b[2] <= mid + 10]    # ends in left half
    right = [b for b in blocks if b[0] >= mid - 10]   # starts in right half
    wide = [b for b in blocks if b not in left and b not in right]

    if len(left) >= 3 and len(right) >= 3:  # two-column page
        order = (sorted(wide, key=lambda b: b[1])
                 + sorted(left, key=lambda b: b[1])
                 + sorted(right, key=lambda b: b[1]))
    else:                                   # single column
        order = sorted(blocks, key=lambda b: (b[1], b[0]))
    return "\n".join(b[4].strip() for b in order)
