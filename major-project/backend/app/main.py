from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import papers, analysis

app = FastAPI(title="Cross-Paper Analysis API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(papers.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
