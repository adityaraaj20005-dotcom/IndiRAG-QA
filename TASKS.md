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

## Current continuation

- [x] Preserve a source-checked 12-question pilot and resumable, budget-limited experiment ledger.
- [ ] Complete paired smoke predictions after the request budget issue is resolved.
- [ ] Complete dashboard, independent annotation, case analysis and deployment security.

## Showcase continuation

- [x] Correct Direct prompt and save a fresh bounded experiment with matched-pair metrics.
- [x] Add team-session access foundation, persistent data path, and basic per-process request limits.
- [x] Add saved-result loading and a comparison display; add six source-checked candidates.
- [ ] Complete pilot after quota recovers; assess unsupported answers and unanswerable cases.
- [ ] Complete dashboard progress/visual QA, broader candidate set, independent review, and deployment security validation.

## Current validation

- [x] Run a retrieval-only evaluation over 15 source-checked answerable variants and save per-question Hybrid rankings.
- [x] Open all seven pages and verify built-in saved-result display in a browser without Gemini calls.
- [ ] Complete browser upload, folder, export download, authentication, and responsive interaction testing.
- [ ] Obtain diverse source documents and independently review a larger benchmark; complete 15 distinct difficult-case analyses.
- [ ] Configure and test an HTTPS same-origin API proxy and persistent production volume before deployment.

## Release preparation

- [x] Default the QA Workspace to retrieval-only; verify a browser query and all four retrieval columns with disposable local data.
- [x] Add same-origin container configuration, production fail-closed settings, revocable single-worker team sessions, a Windows launcher and academic outlines.
- [x] Test secure cookie flags, logout/replay rejection, session expiry, and local-copy public corpus seeding through HTTP/application tests.
- [ ] Verify the built container and HTTPS hosting, persistent disk, final-domain cookie flow, reverse-proxy rate limits, file scanning and backup policy before deployment.
- [ ] Verify browser folder/file selection, removal, authentication interaction, download completion and mobile layouts in the target browser.
- [ ] Review tracked team names and student identifiers and approve the private repository before publishing.

## Final release round

- [x] Add retrieval-only default, saved-result demo, a launcher, IEEE paper and presentation outlines.
- [x] Exercise all four retrieval methods in the browser; test production cookie attributes, session expiry and logout invalidation through local HTTP tests.
- [x] Scan reachable Git blobs for selected secret signatures and excluded paths; record personal information for owner review.
- [ ] Validate browser file/folder uploads, deletion and authentication; verify export actually downloads and test mobile interactions.
- [ ] Build and test the Docker image, real HTTPS domain and persistent storage; review file scanning and shared rate limiting before any public deployment.
