# IndiRAG-QA research summary

## Architecture

The Vite frontend calls a FastAPI service. PyMuPDF extracts PDF text, which is segmented into overlapping passages with page and collection metadata. BM25 and TF-IDF provide lexical baselines; multilingual MiniLM supplies dense retrieval; Hybrid combines BM25 and dense ranks using reciprocal rank fusion. Gemini can synthesize an answer from retrieved evidence. Citation-ID validation checks membership in retrieved passages, not entailment.

## Data and method

The QA pilot contains 12 source-checked questions (nine answerable and three deliberately unanswerable), and six additional candidate questions are source-checked. None has independent human review. The 15 answerable questions cover five fact families; language variants share facts and are not independent samples. Gold passage IDs are checked against the active local collection. Source URLs are recorded in `datasets/qa_pilot_evidence.md`. Reseeding changes document IDs and requires a new gold mapping.

For the local retrieval-only experiment, each answerable question was searched within the scholarship collection at K=5. Recall, precision, hit rate and reciprocal rank use the annotated passage IDs, not semantic equivalence. Results are saved with rankings in `results/retrieval_source_checked.json`.

| Method | Recall@5 | Precision@5 | Hit rate@5 | MRR@5 |
|---|---:|---:|---:|---:|
| BM25 | 0.6667 | 0.1333 | 0.6667 | 0.4889 |
| TF-IDF | 0.6667 | 0.1333 | 0.6667 | 0.4389 |
| Dense | 0.7333 | 0.1467 | 0.7333 | 0.5167 |
| Hybrid | 0.8000 | 0.1600 | 0.8000 | 0.5889 |

These numbers are different from the preserved historical 12-question retrieval pilot because the questions and gold labels differ. Annotating only one of several supporting passages can undercount retrieval success; for example, two income queries miss the FAQ gold ID but retrieve the corroborating guidelines passage.

## QA observations

The corrected Gemini experiment stopped after HTTP 429: nine matched answerable pairs and one failed request. On matched pairs Direct/RAG exact match was 0/0 and token F1 was 0/0.250; all nine RAG answers had structurally valid citation IDs. Direct abstained on all nine. The questions often lack scheme context, and short-reference exact match penalizes verbose answers. There were no completed unanswerable cases; no general hallucination claim is justified. See `results/qa_smoke_corrected.json` and `difficult_cases.md`.

## Limitations and future work

The data is small, source-dependent, and not independently reviewed. The missing unanswerable predictions, no semantic citation verification, no independent support labels, cross-language lexical mismatch, OCR limits, and incomplete difficult-case coverage prevent strong conclusions. Future work should obtain more diverse public sources, verify annotations independently, keep question families in the same split, complete paired evaluations after quota recovers, and conduct blinded citation-support review.
