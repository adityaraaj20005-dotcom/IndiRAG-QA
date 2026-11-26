# Demo guide

## Start and architecture

From the project root, open two PowerShell terminals. In the first run `cd backend`, `.\.venv\Scripts\Activate.ps1`, then `uvicorn main:app --reload --port 8000`. In the second run `cd frontend` and `npm run dev`. Open `http://127.0.0.1:5173`.

This Bennett University CSET 346 project uses a Vite interface and FastAPI backend. PyMuPDF extracts text; BM25 and TF-IDF supply lexical retrieval; Sentence Transformers supplies multilingual dense retrieval; reciprocal rank fusion combines rankings. Gemini generates grounded answers with retrieved citation-ID validation.

## Ten-minute sequence

1. Explain the cross-lingual evidence-grounded QA objective (one minute).
2. Show the document library and scholarship collection (two minutes).
3. Ask “What is the minimum attendance for renewal?”, “नवीनीकरण के लिए न्यूनतम अंक कितने हैं?”, and “Family income limit kitni hai per year?” Inspect evidence (two minutes).
4. Ask “What is the applicant's favourite planet?” and explain that model abstention is not guaranteed (one minute).
5. Compare BM25, TF-IDF, Dense and Hybrid in Retrieval Lab (two minutes).
6. Load the saved retrieval results and corrected QA result JSON separately in Evaluation (two minutes).

The historical retrieval pilot reports Hybrid Recall@5 0.9583 and MRR@5 0.7694. The corrected QA run stopped at HTTP 429 after nine matched answerable pairs. RAG token F1 was 0.250 and citation IDs were valid in 9/9; Direct token F1 was 0. These are incomplete pilot observations, not evidence of general superiority. Citation-ID validity does not establish entailment.

## Viva questions

- Why hybrid retrieval? Lexical and dense methods capture different signals; reciprocal rank fusion combines ranks without assuming their scores are comparable.
- What is MRR? The mean reciprocal rank of the first relevant retrieved passage, or zero when none is retrieved.
- Does a valid citation prove correctness? No; it establishes that the ID belongs to retrieved evidence, not semantic support.
- Why separate API failures? A failed call is neither an answer nor an abstention.
- Why not claim hallucination reduction? The benchmark is incomplete and lacks independent support annotations.

1. Start the backend and frontend using the commands in `README.md`.
2. Open the QA Workspace, select a collection, ask an English, Hindi, or Hinglish question, and inspect validated citation IDs.
3. Use Retrieval Lab to compare BM25, TF-IDF, Dense, and Hybrid results.
4. In Evaluation, upload `research/datasets/indirag_pilot_benchmark.json` for retrieval results.
5. For QA evaluation, upload a manually annotated dataset based on `qa_annotation_template.json`; explicitly confirm live Gemini use before running the small smoke test.
