# Deployment

## Frontend (Vercel)

Deploy `frontend/` as the project root. Set `VITE_API_BASE_URL` to the HTTPS URL of the API, then run `npm ci && npm run build`. The supplied `vercel.json` allows the multipage static app to be served unchanged.

## Backend (Render or equivalent)

Use `render.yaml` or deploy the repository with `pip install -r backend/requirements.txt` and `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`. Store `GEMINI_API_KEY` in the host secret manager, never in Git. Set `GEMINI_MODEL` and `ALLOWED_ORIGINS` to the exact frontend origins. The Docker image deliberately excludes the local PDF corpus and indexes; attach persistent storage and ingest approved documents after deployment.

## Team access and storage

Set `INDIRAG_PRODUCTION=true`, `INDIRAG_AUTH_ENABLED=true`, a strong `INDIRAG_TEAM_PASSWORD` of at least 16 characters and an independent random `INDIRAG_SESSION_SECRET` of at least 32 characters in the host secret manager. Set `ALLOWED_ORIGINS` to exact HTTPS frontend origins. The HTTP-only signed session grants access to the shared team workspace. Cross-site cookie restrictions can prevent authentication in some browsers; verify on the intended hosting domains.

Set `INDIRAG_DATA_DIR` to a persistent mounted directory for PDFs and indexes. Back up that volume independently. The in-process rate limit is per worker, so use one worker for a demonstration and a shared reverse-proxy limiter for public deployment. Production mode fails to start without authentication and HTTPS CORS configuration.

## Before making it public

The team password grants access to every document. Before public deployment, add a hardened shared rate limiter, file scanning, operational logging, a document review policy, and tested backups. Treat PDF text as untrusted prompt input. PyTorch and the multilingual model require substantial memory and cold-start time; measure on the selected host. No public deployment has been verified.
