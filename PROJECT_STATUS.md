# Project status

Retrieval indexing, scoped document operations, four retrieval methods, evidence-grounded query generation, and retrieval evaluation are implemented. The research evaluation layer now supports a separate, opt-in QA evaluation contract and Direct Gemini versus RAG runs.

No QA metrics or difficult-case findings have been fabricated. The next research step is manual annotation from the indexed source passages, followed by a user-approved smoke evaluation.

Update: a 12-question source-checked pilot and one paired live probe exist. The full experiment, expanded dataset, dashboard, and case analysis remain unfinished. Pilot annotations require independent human review.

Continuation: a resumable partial experiment is saved in research/results/qa_smoke_resumable.json. The 24-request ceiling was reached conservatively after reserving nine possible prior attempts. A OneDrive replacement error interrupted a checkpoint; recovery retained the higher request reservation. Public deployment is not ready: authentication, authorization and rate limiting remain outstanding.
