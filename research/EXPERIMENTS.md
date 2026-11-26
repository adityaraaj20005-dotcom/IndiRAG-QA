# Experiments

The included 12-row pilot is retrieval-only: it has gold passage IDs but no reference answers, so it must not be used for QA quality claims. Historical retrieval output is preserved in `research/results/indirag-retrieval-results.json`.

For QA experiments, annotate copies of `research/datasets/qa_annotation_template.json`, validate every passage ID against `/api/documents`, and first submit a small smoke test. The UI requires a live-Gemini confirmation before calling the QA endpoint. Exported result JSON includes per-question predictions and failures.
