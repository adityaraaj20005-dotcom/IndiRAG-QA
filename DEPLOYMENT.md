# Deployment

## Frontend (Vercel)

Deploy `frontend/` as the project root. Set `VITE_API_BASE_URL` to the HTTPS URL of the API, then run `npm ci && npm run build`. The supplied `vercel.json` allows the multipage static app to be served unchanged.

## Backend (Render or equivalent)

Use `render.yaml` or deploy the repository with `pip install -r backend/requirements.txt` and `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`. Store `GEMINI_API_KEY` in the host secret manager, never in Git. Set `GEMINI_MODEL` and `ALLOWED_ORIGINS` to the exact frontend origins.

## Before making it public

The current upload/delete API is intentionally suitable only for a trusted demonstration. Add authentication and per-user/collection authorization, file scanning, request limits/rate limiting, object storage with persistent volumes, logging, and an upload review policy. Treat PDF text as untrusted prompt input. Provision enough RAM for PyTorch/Sentence Transformers and warm-up latency.
