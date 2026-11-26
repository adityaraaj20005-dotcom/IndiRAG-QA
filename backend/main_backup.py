
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from typing import Literal
from sentence_transformers import SentenceTransformer

import fitz  # PyMuPDF
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi


# --------------------------------------------------
# Paths and application configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    content = await file.read()

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
    retrieval_method: Literal["BM25", "Dense"] = "BM25"
    collection_id: str | None = None




@app.post("/api/query")
def query_documents(request: QueryRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Enter a non-empty question.",
        )

    # Restrict the search corpus before ranking any passages.
    if request.collection_id:
        search_passages = [
            item for item in passages
            if item.get("collection_id", "uploaded-pdfs")
            == request.collection_id
        ]
    else:
        search_passages = passages

    if not search_passages:
        raise HTTPException(
            status_code=409,
            detail=(
                "No indexed passages exist in the selected folder. "
                "Upload PDFs to that folder first."
            ),
        )

    query_tokens = tokenize(question)

    if not query_tokens:
        raise HTTPException(
            status_code=400,
            detail="The question contains no searchable tokens.",
        )

    # -----------------------------------------------
    # BM25: lexical retrieval
    # -----------------------------------------------
    if request.retrieval_method == "BM25":
        vocabulary = {
            token
            for item in search_passages
            for token in tokenize(item["text"])
        }

        has_overlap = bool(set(query_tokens) & vocabulary)

        if not has_overlap:
            scores = np.zeros(len(search_passages))
            ranked_indices = []
        else:
            # Use the existing index for all documents.
            if not request.collection_id:
                scores = bm25_index.get_scores(query_tokens)
            else:
                # Build a BM25 index over only the selected folder.
                scoped_tokens = [
                    tokenize(item["text"])
                    for item in search_passages
                ]
                scoped_index = BM25Okapi(scoped_tokens)
                scores = scoped_index.get_scores(query_tokens)

            ranked_indices = np.argsort(scores)[::-1].tolist()

    # -----------------------------------------------
    # Dense: multilingual semantic retrieval
    # -----------------------------------------------
    else:
        model = get_embedding_model()
        passage_vectors = get_dense_embeddings(search_passages)

        query_vector = model.encode(
            [question],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]

        scores = passage_vectors @ query_vector
        ranked_indices = np.argsort(scores)[::-1].tolist()

    # -----------------------------------------------
    # Return supporting passages from the selected scope
    # -----------------------------------------------
    evidence = []

    for index in ranked_indices[:request.top_k]:
        item = search_passages[index]
        score = float(scores[index])

        evidence_item = {
            "passage_id": item["passage_id"],
            "doc_id": item["doc_id"],
            "source": item["document_name"],
            "page": item["page"],
            "text": item["text"],
            "collection_id": item.get(
                "collection_id", "uploaded-pdfs"
            ),
            "collection_name": item.get(
                "collection_name", "Uploaded PDFs"
            ),
            "score": round(score, 5),
        }

        if request.retrieval_method == "BM25":
            evidence_item["bm25_score"] = round(score, 4)

        evidence.append(evidence_item)

    return {
        "question": question,
        "retrieval_method": request.retrieval_method,
        "collection_id": request.collection_id,
        "retrieval_status": (
            "EVIDENCE_FOUND"
            if evidence
            else "NO_MATCHING_PASSAGES"
        ),
        "answerability": "NOT_EVALUATED",
        "answer": None,
        "evidence": evidence,
        "message": (
            "Evidence retrieved successfully. "
            "Answer generation and calibrated answerability "
            "detection have not yet been implemented."
        ),
    }

