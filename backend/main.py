import json
import os
import hmac
import time
from collections import defaultdict, deque
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from typing import Literal
from sentence_transformers import SentenceTransformer
from retrieval import retrieve
from rag_engine import generate
from language_utils import detect_language
from evaluation import evaluate
from qa_evaluation import run_pipeline
from direct_llm import generate_direct, generate_with_evidence
import pymupdf as fitz  # PyMuPDF
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
# --------------------------------------------------
# Paths and application configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("INDIRAG_DATA_DIR") or str(PROJECT_ROOT / "data")).resolve()
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PASSAGES_FILE = PROCESSED_DIR / "passages.jsonl"
DOCUMENTS_FILE = PROCESSED_DIR / "documents.json"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
for folder in (RAW_DIR, PROCESSED_DIR):
    folder.mkdir(parents=True, exist_ok=True)
# --------------------------------------------------
# FastAPI application
# --------------------------------------------------
app = FastAPI(
    title="IndiRAG-QA API",
    description=(
        "Document processing and lexical retrieval for "
        "evidence-grounded multilingual question answering."
    ),
    version="0.1.0",
)
AUTH_ENABLED = os.getenv('INDIRAG_AUTH_ENABLED', 'false').lower() == 'true'
TEAM_PASSWORD = os.getenv('INDIRAG_TEAM_PASSWORD', '')
SESSION_SECRET = os.getenv('INDIRAG_SESSION_SECRET', '')
PRODUCTION = os.getenv('INDIRAG_PRODUCTION', 'false').lower() == 'true'
if (PRODUCTION and not AUTH_ENABLED) or (AUTH_ENABLED and (len(TEAM_PASSWORD) < 16 or len(SESSION_SECRET) < 32)):
    raise RuntimeError('Authentication requires a team password of at least 16 characters and a session secret of at least 32 characters; production requires authentication.')
ORIGINS = [origin.strip() for origin in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if origin.strip()]
if PRODUCTION and (not ORIGINS or '*' in ORIGINS or any(not x.startswith('https://') for x in ORIGINS)):
    raise RuntimeError('Production CORS requires explicit HTTPS origins.')
request_times = defaultdict(deque)

@app.middleware('http')
async def access_control(request: Request, call_next):
    path = request.url.path
    if path.startswith('/api/') and request.method != 'OPTIONS':
        origin = request.headers.get('origin')
        if origin and origin not in ORIGINS:
            return JSONResponse({'detail': 'Origin not allowed.'}, status_code=403)
        if AUTH_ENABLED and path not in ('/api/health', '/api/login') and not request.session.get('authenticated'):
            return JSONResponse({'detail': 'Login required.'}, status_code=401)
        if path in ('/api/login', '/api/query', '/api/evaluation/qa'):
            key = (request.client.host if request.client else 'unknown', path)
            now = time.monotonic(); q = request_times[key]
            while q and q[0] < now - 60: q.popleft()
            if len(q) >= (5 if path == '/api/login' else 20):
                return JSONResponse({'detail': 'Rate limit exceeded.'}, status_code=429)
            q.append(now)
    return await call_next(request)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET or 'local-development-only', https_only=PRODUCTION, same_site='none' if PRODUCTION else 'lax', max_age=28800)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    password: str = Field(max_length=256)

@app.post('/api/login')
def login(request: Request, credentials: LoginRequest):
    if not AUTH_ENABLED or not hmac.compare_digest(credentials.password, TEAM_PASSWORD):
        raise HTTPException(status_code=401, detail='Invalid credentials.')
    request.session.clear()
    request.session['authenticated'] = True
    return {'status': 'authenticated'}

@app.post('/api/logout')
def logout(request: Request):
    request.session.clear()
    return {'status': 'signed out'}
# --------------------------------------------------
# In-memory search index + persistent JSON storage
# --------------------------------------------------
documents = []
passages = []
bm25_index = None
corpus_vocabulary = set()
# Multilingual dense-retrieval configuration
EMBEDDING_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
embedding_model = None
dense_embeddings = None
dense_cache_passage_ids = None
def get_embedding_model():
    """Load the embedding model only when dense search is requested."""
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )
    return embedding_model
def get_dense_embeddings(items=None):
    """Encode and cache all passages or a selected collection."""
    global dense_embeddings, dense_cache_passage_ids
    selected_passages = passages if items is None else items
    current_ids = [
        item["passage_id"] for item in selected_passages
    ]
    if not current_ids:
        return None
    if (
        dense_embeddings is None
        or dense_cache_passage_ids != current_ids
    ):
        model = get_embedding_model()
        texts = [item["text"] for item in selected_passages]
        dense_embeddings = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        dense_cache_passage_ids = current_ids.copy()
    return dense_embeddings
def tokenize(text: str) -> list[str]:
    """Basic Unicode-aware tokenization, including Indic text."""
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
def clean_text(text: str) -> str:
    """Normalize PDF-extracted whitespace and line breaks."""
    text = text.replace("\x00", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
def chunk_text(text: str) -> list[str]:
    """Split text into overlapping character-based passages."""
    text = clean_text(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk and tokenize(chunk):
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = end - CHUNK_OVERLAP
        # Prevent an infinite loop if configuration is changed.
        start = max(start + 1, next_start)
    return chunks
def rebuild_index():
    """Rebuild BM25 after loading data or uploading a PDF."""
    global bm25_index, corpus_vocabulary
    tokenized_passages = [
        tokenize(item["text"]) for item in passages
    ]
    valid_items = [
        (item, tokens)
        for item, tokens in zip(passages, tokenized_passages)
        if tokens
    ]
    if len(valid_items) != len(passages):
        passages[:] = [item for item, _ in valid_items]
        tokenized_passages = [tokens for _, tokens in valid_items]
    corpus_vocabulary = {
        token
        for passage_tokens in tokenized_passages
        for token in passage_tokens
    }
    bm25_index = (
        BM25Okapi(tokenized_passages)
        if tokenized_passages
        else None
    )
def save_state():
    """Persist documents and passages across server restarts."""
    DOCUMENTS_FILE.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with PASSAGES_FILE.open("w", encoding="utf-8") as file:
        for passage in passages:
            file.write(
                json.dumps(passage, ensure_ascii=False) + "\n"
            )
def load_state():
    """Load saved metadata and passages when the server starts."""
    global documents, passages
    if DOCUMENTS_FILE.exists():
        documents = json.loads(
            DOCUMENTS_FILE.read_text(encoding="utf-8")
        )
    if PASSAGES_FILE.exists():
        with PASSAGES_FILE.open("r", encoding="utf-8") as file:
            passages = [
                json.loads(line)
                for line in file
                if line.strip()
            ]
    rebuild_index()
load_state()
# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "IndiRAG-QA",
        "indexed_documents": len(documents),
        "indexed_passages": len(passages),
    }
# --------------------------------------------------
# Document listing
# --------------------------------------------------
@app.get("/api/documents")
def list_documents():
    return {
        "count": len(documents),
        "documents": documents,
    }
@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    """Remove a PDF, its passages and its search-index entries."""
    document = next(
        (doc for doc in documents if doc["doc_id"] == document_id),
        None,
    )
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )
    # Remove the document and every associated passage.
    documents[:] = [
        doc for doc in documents
        if doc["doc_id"] != document_id
    ]
    passages[:] = [
        passage for passage in passages
        if passage["doc_id"] != document_id
    ]
    # Delete the stored copy of this PDF, if available.
    stored_filename = document.get("stored_filename")
    if stored_filename:
        safe_filename = Path(stored_filename).name
        stored_path = RAW_DIR / safe_filename
        if stored_path.is_file():
            stored_path.unlink()
    # Rebuild retrieval state and persist the updated library.
    rebuild_index()
    save_state()
    return {
        "message": "Document removed successfully.",
        "deleted_doc_id": document_id,
        "remaining_documents": len(documents),
        "remaining_passages": len(passages),
    }
# --------------------------------------------------
# PDF upload + text extraction + passage segmentation
# --------------------------------------------------
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_id: str = Form(default="uploaded-pdfs"),
    collection_name: str = Form(default="Uploaded PDFs"),
):
    original_name = Path(file.filename or "").name
    if not original_name:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )
    if Path(original_name).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=415,
            detail="Only PDF documents are supported.",
        )
    content = await file.read(MAX_FILE_SIZE + 1)
    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The PDF exceeds the 20 MB upload limit.",
        )
    try:
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to read this PDF. Check that it is a valid, unencrypted PDF.",
        ) from exc
    document_id = uuid.uuid4().hex[:12]
    safe_name = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        original_name,
    )
    stored_name = f"{document_id}_{safe_name}"
    saved_path = RAW_DIR / stored_name
    new_passages = []
    pages_with_text = 0
    try:
        with pdf:
            page_count = len(pdf)
            for page_index, page in enumerate(pdf):
                page_text = clean_text(page.get_text("text"))
                if not page_text:
                    continue
                pages_with_text += 1
                page_chunks = chunk_text(page_text)
                for chunk_index, chunk in enumerate(page_chunks, start=1):
                    new_passages.append({
                        "doc_id": document_id,
                        "passage_id": (
                            f"{document_id}_P{page_index + 1}_"
                            f"C{chunk_index}"
                        ),
                        "document_name": original_name,
                        "collection_id": collection_id,
                        "collection_name": collection_name,
                        "page": page_index + 1,
                        "chunk": chunk_index,
                        "text": chunk,
                    })
        if not new_passages:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No extractable text was found. "
                    "This may be a scanned PDF requiring OCR."
                ),
            )
        saved_path.write_bytes(content)
        document_record = {
            "doc_id": document_id,
            "filename": original_name,
            "collection_id": collection_id,
            "collection_name": collection_name,
            "stored_filename": stored_name,
            "pages": page_count,
            "pages_with_text": pages_with_text,
            "passages": len(new_passages),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        documents.append(document_record)
        passages.extend(new_passages)
        rebuild_index()
        save_state()
        return {
            "message": "PDF processed and indexed successfully.",
            "document": document_record,
            "passage_count": len(new_passages),
        }
    except HTTPException:
        raise
    except Exception as exc:
        # Avoid retaining a partially processed document in memory.
        passages[:] = [
            p for p in passages if p["doc_id"] != document_id
        ]
        documents[:] = [
            d for d in documents if d["doc_id"] != document_id
        ]
        if saved_path.exists():
            saved_path.unlink()
        rebuild_index()
        save_state()
        raise HTTPException(
            status_code=500,
            detail="Document processing failed. Check the server terminal.",
        ) from exc
# --------------------------------------------------
# BM25 lexical retrieval
# --------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    retrieval_method: Literal["BM25", "Dense", "Hybrid", "TF-IDF"] = "BM25"
    collection_id: str | None = None
    generate_answer: bool = True


def scoped_passages(collection_id):
    return [p for p in passages if collection_id is None or p.get("collection_id", "uploaded-pdfs") == collection_id]


@app.post("/api/query")
def query_documents(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Enter a question.")
    items = scoped_passages(request.collection_id)
    if not items:
        raise HTTPException(status_code=409, detail="No passages in selected collection.")
    evidence = retrieve(question, items, request.retrieval_method, request.top_k, get_embedding_model, get_dense_embeddings)
    result = generate(question, evidence) if request.generate_answer else {"answer": None, "answerability": "NOT_EVALUATED", "confidence": None, "citations": [], "message": "Retrieval only."}
    return {"question": question, "language": detect_language(question), "retrieval_method": request.retrieval_method, "collection_id": request.collection_id, "retrieval_status": "EVIDENCE_FOUND" if evidence else "NO_MATCHING_PASSAGES", "evidence": evidence, **result}


@app.post("/api/retrieval/compare")
def compare_retrieval(request: QueryRequest):
    items = scoped_passages(request.collection_id)
    if not items:
        raise HTTPException(status_code=409, detail="No passages in selected collection.")
    return {"question": request.question, "results": {method: retrieve(request.question, items, method, request.top_k, get_embedding_model, get_dense_embeddings) for method in ("TF-IDF", "BM25", "Dense", "Hybrid")}}


class EvaluationRow(BaseModel):
    question: str
    language: str
    relevant_passage_ids: list[str]
    collection_id: str | None = None


class QAEvaluationRow(BaseModel):
    """A manually annotated QA instance; references are never inferred by the API."""
    question: str = Field(min_length=1, max_length=2000)
    language: str
    answerable: bool
    reference_answers: list[str] = Field(default_factory=list)
    relevant_passage_ids: list[str] = Field(default_factory=list)
    collection_id: str | None = None
    source_filenames: list[str] = Field(default_factory=list)
    pages: list[int] = Field(default_factory=list)
    difficulty: str | None = None
    family_id: str | None = None


class QAExperimentRequest(BaseModel):
    rows: list[QAEvaluationRow] = Field(min_length=1, max_length=100)
    pipelines: list[Literal["direct", "rag"]] = Field(default_factory=lambda: ["rag"])
    retrieval_method: Literal["BM25", "Dense", "Hybrid", "TF-IDF"] = "Hybrid"
    top_k: int = Field(default=5, ge=1, le=10)
    confirm_generation: bool = False


def validate_qa_rows(rows: list[QAEvaluationRow]):
    for row in rows:
        if row.answerable and not row.reference_answers:
            raise HTTPException(status_code=422, detail="Answerable QA rows require at least one manually verified reference answer.")
        if not row.answerable and row.reference_answers:
            raise HTTPException(status_code=422, detail="Unanswerable QA rows cannot include reference answers.")
        valid = {p["passage_id"] for p in scoped_passages(row.collection_id)}
        if not set(row.relevant_passage_ids).issubset(valid):
            raise HTTPException(status_code=400, detail="Invalid or out-of-scope QA gold passage ID.")
        if row.answerable and not row.relevant_passage_ids:
            raise HTTPException(status_code=422, detail="Answerable QA rows require verified gold passage IDs.")


@app.post("/api/evaluation/run")
def run_evaluation(rows: list[EvaluationRow]):
    for row in rows:
        valid = {p["passage_id"] for p in scoped_passages(row.collection_id)}
        if not set(row.relevant_passage_ids).issubset(valid):
            raise HTTPException(status_code=400, detail="Invalid or out-of-scope gold passage ID.")
    def search(row, method, k):
        return retrieve(row["question"], scoped_passages(row.get("collection_id")), method, k, get_embedding_model, get_dense_embeddings)
    return {"results": evaluate([row.model_dump() for row in rows], search), "note": "Retrieval-only evaluation; rows without gold passages excluded."}


@app.post("/api/evaluation/qa")
def run_qa_evaluation(request: QAExperimentRequest):
    """Run a small, opt-in live QA experiment and retain per-question traces."""
    if not request.confirm_generation:
        raise HTTPException(status_code=409, detail="Live Gemini generation is opt-in. Review the dataset and resend with confirm_generation=true (start with a small smoke test).")
    validate_qa_rows(request.rows)
    rows = [row.model_dump() for row in request.rows]
    output = {"pipelines": {}, "configuration": {"retrieval_method": request.retrieval_method, "top_k": request.top_k, "n": len(rows)}}
    for pipeline in dict.fromkeys(request.pipelines):
        def runner(row, pipeline=pipeline):
            if pipeline == "direct":
                generated = generate_direct(row["question"])
                return {**generated, "citation_valid": None, "evidence": []}
            items = scoped_passages(row.get("collection_id"))
            evidence = retrieve(row["question"], items, request.retrieval_method, request.top_k, get_embedding_model, get_dense_embeddings)
            generated = generate_with_evidence(row["question"], evidence)
            valid_ids = {p["passage_id"] for p in evidence}
            citations = generated.get("citations", [])
            citation_valid = isinstance(citations, list) and bool(citations) and all(isinstance(value, str) and value in valid_ids for value in citations)
            return {**generated, "citation_valid": citation_valid, "evidence": evidence}
        output["pipelines"][pipeline] = run_pipeline(rows, runner)
    output["note"] = "Only completed calls contribute to metrics. API/generation failures are reported separately and never relabeled as UNANSWERABLE. Unsupported-answer rate requires a separate manual support annotation."
    return output
