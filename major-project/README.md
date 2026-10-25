# Cross-Paper Analysis and Research Gap Discovery

Stage 1: PDF upload + text extraction (page numbers preserved).

## Run backend (PowerShell, from major-project\backend)
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload
Check: http://localhost:8000/health  |  API docs: http://localhost:8000/docs

## Run frontend (second terminal, from major-project\frontend)
    npm install
    npm run dev
Open http://localhost:5173
uvicorn app.main:app --reload