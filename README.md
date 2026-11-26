# IndiRAG-QA

Evidence-grounded cross-lingual QA for English, Hindi, and Hinglish scholarship documents. The system indexes text PDFs, retrieves passages with BM25, TF-IDF, multilingual dense retrieval, or hybrid RRF, and optionally generates Gemini answers with citation-ID checks.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set GEMINI_API_KEY in backend/.env
uvicorn main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. API documentation is at `http://127.0.0.1:8000/docs`.

## Evaluation

The included pilot benchmark is retrieval-only. QA metrics require manually verified answers and gold passage IDs using `research/datasets/qa_annotation_template.json`. The UI and `/api/evaluation/qa` require explicit confirmation before live Gemini evaluation. See `research/METRICS.md`, `research/EXPERIMENTS.md`, and `DEPLOYMENT.md`.
