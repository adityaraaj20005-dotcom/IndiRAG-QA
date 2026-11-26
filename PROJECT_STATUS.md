# Project status

Retrieval indexing, scoped document operations, four retrieval methods, evidence-grounded query generation, and retrieval evaluation are implemented. The research evaluation layer now supports a separate, opt-in QA evaluation contract and Direct Gemini versus RAG runs.

No QA metrics or difficult-case findings have been fabricated. The next research step is manual annotation from the indexed source passages, followed by a user-approved smoke evaluation.

Update: a 12-question source-checked pilot and one paired live probe exist. The full experiment, expanded dataset, dashboard, and case analysis remain unfinished. Pilot annotations require independent human review.

Continuation: a resumable partial experiment is saved in research/results/qa_smoke_resumable.json. The 24-request ceiling was reached conservatively after reserving nine possible prior attempts. A OneDrive replacement error interrupted a checkpoint; recovery retained the higher request reservation. Public deployment is not ready: authentication, authorization and rate limiting remain outstanding.

Latest: corrected experiment stopped at HTTP 429 after 19 reserved attempts with nine matched pairs. The team-authentication foundation, request limits, persistent data path, and saved-result loader were added; public deployment remains unverified. Six additional source-checked candidates have been added; none has independent human review. The dashboard still needs complete live progress and browser-level verification.

Retrieval-only source-checked experiment: 15 answerable questions, Hybrid Recall@5 0.8000; results and case traces are saved. All seven pages were opened in a browser, but full interactive, mobile, folder upload and export verification remains incomplete. No new Gemini calls were made.

Release preparation: the QA workspace now defaults to retrieval-only, and the Dockerfile is configured to serve the built frontend and API together with production authentication enabled. Local production-mode HTTP tests verified secure session-cookie attributes and logout; the real HTTPS host and Docker build remain untested. A disposable browser test confirmed collection-scoped BM25 retrieval and all four Retrieval Lab columns. Browser file chooser, folder upload, authentication interaction, and download confirmation remain unverified. The locally copied public corpus seeded successfully; the official download URL returned 404 in this environment. No Gemini calls were made.

Final release round: the single-worker session registry invalidates logged-out and expired sessions; Docker startup fails closed without production credentials and a configured data path. The local same-origin ASGI test returned the frontend, authenticated API and secure cookie flags successfully, but does not verify real TLS or deployed cookies. A historical Git pattern scan found no selected credential signatures or excluded corpus paths; it is not comprehensive. Team names and student identifiers remain tracked on the About and landing pages and need owner review before sharing. One Windows test process used about 1,160 MiB working set and 2,393 MiB private memory with one passage and the embedding model loaded; Linux container peak is unmeasured.
