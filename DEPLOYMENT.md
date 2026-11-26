# Deployment

## Frontend (Vercel)

Deploy `frontend/` as the project root. Set `VITE_API_BASE_URL` to the HTTPS URL of the API, then run `npm ci && npm run build`. The supplied `vercel.json` allows the multipage static app to be served unchanged.

## Backend (Render or equivalent)

Use `render.yaml` or deploy the repository with `pip install -r backend/requirements.txt` and `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`. Store `GEMINI_API_KEY` in the host secret manager, never in Git. Set `GEMINI_MODEL` and `ALLOWED_ORIGINS` to the exact frontend origins. The Docker image deliberately excludes the local PDF corpus and indexes; attach persistent storage and ingest approved documents after deployment.

## Team access and storage

Set `INDIRAG_PRODUCTION=true`, `INDIRAG_AUTH_ENABLED=true`, a strong `INDIRAG_TEAM_PASSWORD` of at least 16 characters and an independent random `INDIRAG_SESSION_SECRET` of at least 32 characters in the host secret manager. Set `ALLOWED_ORIGINS` to exact HTTPS frontend origins. The HTTP-only signed session grants access to the shared team workspace. Cross-site cookie restrictions can prevent authentication in some browsers; verify on the intended hosting domains.

Set `INDIRAG_DATA_DIR` to a persistent mounted directory for PDFs and indexes. Back up that volume independently. The in-process rate limit is per worker, so use one worker for a demonstration and a shared reverse-proxy limiter for public deployment. Production mode fails to start without authentication and HTTPS CORS configuration.

## Reproducible public corpus

`backend/seed_public_corpus.py` downloads two official Ministry of Education PDFs documented in `research/datasets/qa_pilot_evidence.md`. To seed a new dedicated empty directory, in PowerShell set `$env:INDIRAG_DATA_DIR` to its absolute path, set `$env:INDIRAG_PRODUCTION='false'` and `$env:INDIRAG_AUTH_ENABLED='false'`, then from `backend/` run `python seed_public_corpus.py`. Do this offline before starting the secured service; restore production environment settings before serving. The script refuses a nonempty target. Generated document IDs differ from existing benchmark IDs; relabel or map gold IDs before rerunning evaluation. Never copy a private local index into a public image.

## Frontend and cross-origin sessions

Production frontend builds default to same-origin `/api`. Before deployment, configure the hosting provider's HTTPS reverse proxy to forward `/api/*` to the backend without exposing backend credentials; validate cookie and origin behavior on the final domains. Alternatively `VITE_API_BASE_URL` may target an HTTPS backend, but cross-site cookie blocking can break sessions. The supplied Vercel configuration does not yet establish an API proxy; set and test its destination after a backend hostname exists. No hosting configuration here has been deployed or tested end-to-end.

CPU-only PyTorch and multilingual MiniLM consume substantial memory. Model and embeddings load lazily; the 46-passage local corpus is much smaller than a production corpus. Memory depends on OS, package builds, model cache and concurrency; no reliable deployment peak was measured in this round. Measure cold start and peak RAM with the final image before selecting a host. Use persistent disk for the model cache if appropriate.

## Publishing after approval

Review `git status`, `git ls-files`, and the staged diff for secrets and private data. Create a private or public GitHub repository only after deciding its visibility, then add the intended remote using `git remote add origin <repository-url>` and push the reviewed branch using `git push -u origin <branch>`. Do not place credentials in the remote URL. Configure the HTTPS proxy, host secrets, persistent storage, and permitted origins before deploying; test login, upload restrictions, and logout on the deployed domains. None of those external actions has been performed.

## Before making it public

The team password grants access to every document. Before public deployment, add a hardened shared rate limiter, file scanning, operational logging, a document review policy, and tested backups. Treat PDF text as untrusted prompt input. PyTorch and the multilingual model require substantial memory and cold-start time; measure on the selected host. No public deployment has been verified.
