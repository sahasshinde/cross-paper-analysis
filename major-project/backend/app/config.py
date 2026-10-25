"""Central settings. Change the embedding model here, nowhere else."""
import os
from pathlib import Path

# Any Sentence-Transformers model name works here.
# "all-MiniLM-L6-v2" is ~5x faster (use it if your laptop is slow).
EMBEDDING_MODEL = "all-mpnet-base-v2"

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Optional: wording of gaps by a LOCAL open-source LLM through Ollama (free, offline).
# Disabled by default; gaps are then worded by a built-in template.
# To enable (PowerShell, before starting uvicorn):  $env:OLLAMA_MODEL="llama3.2:3b"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
