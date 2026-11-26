# IndiRAG-QA implementation checklist

- [x] Audit existing API, frontend, pilot benchmark, and historical retrieval results.
- [x] Add Git hygiene that excludes secrets and local/private PDF data.
- [x] Preserve retrieval evaluation API and pilot benchmark.
- [x] Add Unicode-aware QA metrics, answerability confusion matrix, latency, language groups, and citation-ID validity.
- [x] Add opt-in Direct Gemini vs RAG experiment endpoint with retries and per-question traces.
- [x] Add a manually verified QA annotation template.
- [x] Add unit tests for multilingual metric behavior and generation failures.
- [ ] Create 300–500 manually verified QA instances after source review and annotation.
- [ ] Run a user-approved, quota-aware QA smoke experiment, then a full experiment.
- [ ] Write difficult-case analysis from actual saved prediction traces (minimum 15 cases).
- [ ] Add authentication/shared-access controls before public document upload deployment.
