# Difficult-case review workflow

Review the actual `predictions` and `evidence` in `results/qa_smoke_resumable.json`. For each selected case, record question, reference answers, retrieved passage IDs and text, direct and RAG answers, citations, outcome, error category, and an evidence-based explanation. Categories include retrieval failure, language mismatch, unsupported answer, invalid citation, and successful abstention. Do not infer semantic support from citation-ID validity alone.

Fifteen-case target: pending independent review. The first paired English question in `qa_smoke_probe.json` was an observed direct abstention and RAG answer; the original evidence trace was not saved in that probe. Remaining cases must be selected and analyzed from the retained records.
