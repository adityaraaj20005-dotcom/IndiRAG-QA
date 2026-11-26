# Deployment

## Frontend (Vercel)

The preferred prepared configuration serves the built frontend from FastAPI in one Docker service, with `/api` on the same HTTPS origin. The Vercel configuration is static-only and does not proxy `/api`; do not deploy it separately until an explicit HTTPS reverse proxy is configured and tested.

## Backend (Render or equivalent)

The prepared `render.yaml` uses the multi-stage Dockerfile, port 8000 and `/api/health`. It serves the frontend and API together. Store `GEMINI_API_KEY` in the host secret manager, never in Git. Set `GEMINI_MODEL` and `ALLOWED_ORIGINS` to the exact HTTPS site origin. Attach persistent storage and set its absolute mount path as `INDIRAG_DATA_DIR`. The image excludes local PDFs and indexes. Docker and an actual HTTPS host were not available for end-to-end verification in this workspace.

## Team access and storage

Set `INDIRAG_PRODUCTION=true`, `INDIRAG_AUTH_ENABLED=true`, a strong `INDIRAG_TEAM_PASSWORD` of at least 16 characters and an independent random `INDIRAG_SESSION_SECRET` of at least 32 characters in the host secret manager. Set `ALLOWED_ORIGINS` to exact HTTPS frontend origins. The HTTP-only signed session grants access to the shared team workspace. Cross-site cookie restrictions can prevent authentication in some browsers; verify on the intended hosting domains.

Set `INDIRAG_DATA_DIR` to an absolute persistent mounted directory for PDFs and indexes. Back up that volume independently. The in-process rate limit and session registry are per worker, so use one worker for a demonstration and a shared reverse-proxy limiter for public deployment. Sessions expire after eight hours, logout invalidates the server-side session, and a restart invalidates all sessions. Production mode fails to start without authentication, an absolute data path and explicit HTTPS CORS origins. Production cookies are Secure, HttpOnly and SameSite=None. TLS must terminate at a trusted HTTPS host.

## Reproducible public corpus

`backend/seed_public_corpus.py` can use two approved official PDFs documented in `research/datasets/qa_pilot_evidence.md`. In the current environment the automatic official URL returned HTTP 404, so use verified local public copies: set `$env:INDIRAG_DATA_DIR` to a dedicated empty directory, `$env:INDIRAG_PRODUCTION='false'` and `$env:INDIRAG_AUTH_ENABLED='false'`; then from `backend/` run `python seed_public_corpus.py --faq <faq.pdf> --guidelines <guidelines.pdf>`. A local-copy seed was tested and indexed 26 and 11 passages. Restore production settings before serving. The script records source URLs and hashes, but cannot establish a local file's provenance; review the files first. Generated document IDs differ from historical benchmark IDs; relabel or map gold IDs before rerunning evaluation.

## Frontend and cross-origin sessions

Production frontend builds default to same-origin `/api`; the Docker image bundles and serves both on one host, avoiding cross-site cookies and a separate proxy. For separate Vercel hosting an explicit `/api/*` HTTPS reverse proxy is still required. No hosting configuration here has been deployed or tested end-to-end.

One Windows test process with the model loaded and one indexed passage used approximately 1,160 MiB working set and 2,393 MiB private committed memory at one observation. This is not a peak or a Linux container measurement. A conservative initial sizing estimate is at least 4 GiB RAM and two CPU cores for one worker, with additional headroom for concurrency, model loading and the OS; actual needs may be higher. Benchmark the final image and corpus before choosing or purchasing a host. Persist the model cache if appropriate.

## Publishing after approval

Review `git status`, `git ls-files`, and the staged diff for secrets and private data. Create a private or public GitHub repository only after deciding its visibility, then add the intended remote using `git remote add origin <repository-url>` and push the reviewed branch using `git push -u origin <branch>`. Do not place credentials in the remote URL. Configure the HTTPS proxy, host secrets, persistent storage, and permitted origins before deploying; test login, upload restrictions, and logout on the deployed domains. None of those external actions has been performed.

## Before making it public

The team password grants access to every document. Before public deployment, add a hardened shared rate limiter, proxy-level request-body limits, PDF malware scanning, operational logging, a document review policy, and tested backups. The application checks file extension, parsing and a 20 MiB application read limit; it does not scan for malware and the multipart body may be buffered before application validation. Treat PDF text as untrusted prompt input. No public deployment has been verified.
