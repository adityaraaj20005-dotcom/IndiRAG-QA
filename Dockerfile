FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
COPY --from=frontend-build /frontend/dist /app/frontend-dist
ENV PYTHONUNBUFFERED=1 INDIRAG_PRODUCTION=true INDIRAG_AUTH_ENABLED=true INDIRAG_FRONTEND_DIR=/app/frontend-dist
EXPOSE 8000
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
