# Experiments

The included 12-row pilot is retrieval-only: it has gold passage IDs but no reference answers, so it must not be used for QA quality claims. Historical retrieval output is preserved in `research/results/indirag-retrieval-results.json`.

For QA experiments, annotate copies of `research/datasets/qa_annotation_template.json`, validate every passage ID against `/api/documents`, and first submit a small smoke test. The UI requires a live-Gemini confirmation before calling the QA endpoint. Exported result JSON includes per-question predictions and failures.

The corrected pilot is saved as `results/qa_smoke_corrected.json`, separate from the historical partial run. HTTP 429 stopped it after 19 reserved attempts and nine matched successful pairs, all answerable. Direct had no document context; its general knowledge differs from document answerability. These incomplete results do not support a full-pilot comparison.
