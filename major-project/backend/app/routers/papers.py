from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException
from app.config import UPLOAD_DIR
from app.services.pdf_service import extract_pages

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/upload")
async def upload(files: list[UploadFile]):
    if len(files) < 2:
        raise HTTPException(400, "Upload at least 2 papers.")
    papers = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{f.filename} is not a PDF.")
        dest = UPLOAD_DIR / Path(f.filename).name
        dest.write_bytes(await f.read())
        pages = extract_pages(dest)
        papers.append({
            "name": f.filename,
            "num_pages": len(pages),
            "preview": pages[0]["text"][:600] if pages else "",
        })
    return {"papers": papers}
