from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import UPLOAD_DIR
from app.services.extraction_service import analyze_paper
from app.services.similarity_service import compare_aspects
from app.services.clustering_service import cluster_statements
from app.services.gap_service import build_gaps
from app.services import llm_service
from app import config

router = APIRouter(prefix="/analysis", tags=["analysis"])


class PaperList(BaseModel):
    filenames: list[str]


def _path(name):
    path = UPLOAD_DIR / Path(name).name
    if not path.exists():
        raise HTTPException(404, f"{name} not found. Upload it again.")
    return path


# plain "def" (not async): FastAPI runs it in a worker thread, so the
# slow model work does not freeze the server.
@router.post("/aspects")
def aspects(req: PaperList):
    papers = []
    for n in req.filenames:
        r = analyze_paper(_path(n))
        papers.append({"name": n, **{k: v for k, v in r.items() if not k.startswith("_")}})
    return {"papers": papers}


@router.post("/compare")
def compare(req: PaperList):
    if len(req.filenames) < 2:
        raise HTTPException(400, "Select at least 2 papers to compare.")
    papers = []
    for n in req.filenames:
        r = analyze_paper(_path(n))
        papers.append({"name": n, "pool": r["pool"], "facts": r["dataset_facts"]})
    return compare_aspects(papers)


class ClusterRequest(BaseModel):
    filenames: list[str]
    threshold: float | None = None      # grouping strictness; None = automatic


@router.post("/clusters")
def clusters(req: ClusterRequest):
    if len(req.filenames) < 2:
        raise HTTPException(400, "Select at least 2 papers.")
    papers = [{"name": n, "pool": analyze_paper(_path(n))["pool"]} for n in req.filenames]
    return cluster_statements(papers, req.threshold)


@router.post("/gaps")
def gaps(req: ClusterRequest):
    if len(req.filenames) < 2:
        raise HTTPException(400, "Select at least 2 papers.")
    results = {n: analyze_paper(_path(n)) for n in req.filenames}
    papers = [{"name": n, "pool": r["pool"]} for n, r in results.items()]
    clusters = cluster_statements(papers, req.threshold)
    pages = {n: r["_pages"] for n, r in results.items()}
    return {
        "model": clusters["model"], "threshold": clusters["threshold"],
        "total_papers": clusters["total_papers"], "num_statements": clusters["num_statements"],
        "wording": ("local LLM (" + config.OLLAMA_MODEL + ") with template fallback")
                   if llm_service.is_enabled() else "template",
        "gaps": build_gaps(clusters, pages),
    }
