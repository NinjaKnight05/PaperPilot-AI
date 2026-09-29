from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

import uuid
from app.services.pdf_processor import extract_text_from_pdf
from app.services.chunker import chunk_documents
from app.services.vector_strore import create_vectors
from dotenv import load_dotenv
load_dotenv()
from app.services.rag_pipeline import is_relevant_to_pdf, ask_with_resources
from app.services.verifier import verify_answer
from app.memory import get_history, add_to_history, format_history
from app.services.router import classify_query
from app.services.llm import answer_general
from app.services.web import answer_web
from app.services.vision import answer_vision

app = FastAPI(
    title="Advanced PDF RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://paperpilot-ai-sigma.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


@app.get("/")
def home():
    return {
        "message": "Advanced PDF RAG is running"
    }


def _resolve_document(document_id: str):
    """Given a document_id, find its file on disk and figure out whether
    it's a PDF or an image, by checking whatever extension it was saved with."""
    matches = list(UPLOAD_DIR.glob(f"{document_id}.*"))
    if not matches:
        return None, None
    path = matches[0]
    kind = "pdf" if path.suffix.lower() == ".pdf" else "image"
    return kind, path


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), session_id: str | None = None):

    if file.content_type == "application/pdf":
        kind = "pdf"
    elif file.content_type in IMAGE_CONTENT_TYPES:
        kind = "image"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF or image files (jpg, png, webp) are allowed"
        )

    if session_id is None:
        session_id = str(uuid.uuid4())

    document_id = str(uuid.uuid4())

    if kind == "pdf":
        ext = ".pdf"
    else:
        orig_ext = Path(file.filename or "").suffix.lower()
        ext = orig_ext if orig_ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"

    file_path = UPLOAD_DIR / f"{document_id}{ext}"

    content = await file.read()
    file_path.write_bytes(content)

    pages = None
    chunks_count = None

    if kind == "pdf":
        documents = extract_text_from_pdf(file_path)
        chunks = chunk_documents(documents)
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
        create_vectors(chunks)
        pages = len(documents)
        chunks_count = len(chunks)

    (UPLOAD_DIR / f"session_{session_id}.txt").write_text(document_id)

    return {
        "message": f"{'PDF' if kind == 'pdf' else 'Image'} uploaded successfully",
        "session_id": session_id,
        "document_id": document_id,
        "filename": file.filename,
        "kind": kind,
        "pages": pages,
        "chunks": chunks_count
    }


RECENCY_WORDS = ("latest", "current", "today", "now", "recent", "up to date", "up-to-date")


DOC_WORDS = (
    "this pdf", "the pdf", "my pdf",
    "this document", "the document", "my document",
    "this paper", "the paper",
    "this file", "the file",
    "this image", "the image", "my image",
    "this photo", "the photo",
    "this picture", "the picture",
)


OVERVIEW_WORDS = ("about", "explain", "summar", "overview", "what is this")

OVERVIEW_QUERY = (
    "What is this document about? Give an overview of its abstract, "
    "introduction, main topics and conclusion."
)

FOLLOWUP_WORDS = {"it", "this", "that", "more", "again", "elaborate", "further", "explain", "u"}

def needs_rewrite(question: str, history_text: str) -> bool:
    if not history_text:
        return False
    words = question.lower().split()
    return len(words) <= 4 or any(w.strip("?.!,") in FOLLOWUP_WORDS for w in words)

def has_recency_signal(question: str) -> bool:
    q = question.lower()
    return any(word in q for word in RECENCY_WORDS)


def mentions_document(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in DOC_WORDS)


def is_overview_question(question: str) -> bool:
    q = question.lower()
    return mentions_document(q) and any(w in q for w in OVERVIEW_WORDS)


@app.post("/ask")
def ask_questions(
    question: str,
    session_id: str,
    document_id: str | None = None,
    mode: str = "smart"
):
    has_document = False
    session_file = UPLOAD_DIR / f"session_{session_id}.txt"

    if document_id is None and session_file.exists():
        document_id = session_file.read_text().strip()

    doc_kind, doc_path = (None, None)
    if document_id is not None:
        doc_kind, doc_path = _resolve_document(document_id)
        has_document = doc_kind is not None

    search_q = question

    if doc_kind == "image":
        history_key = f"{session_id}_{document_id}"
        history_text = format_history(get_history(history_key))
        answer = answer_vision(question, doc_path, history_text)
        add_to_history(history_key, question, answer)
        return {
            "question": question,
            "document_id": document_id,
            "mode": mode,
            "answered_using": "vision",
            "answer": answer,
            "sources": None,
            "verified": None
        }

    if mode == "pdf_only":
        if not has_document:
            raise HTTPException(status_code=400, detail="No document uploaded.")
        route = "pdf"
        if is_overview_question(question):
            search_q = OVERVIEW_QUERY
    else:
        if has_document and is_overview_question(question):
            route = "pdf"
            search_q = OVERVIEW_QUERY
        elif has_document and mentions_document(question):
            route = "pdf"
        else:
            pdf_relevant = has_document and is_relevant_to_pdf(question, document_id)

            if pdf_relevant and has_recency_signal(question):
                route = "web"
            elif pdf_relevant:
                route = "pdf"
            else:
                route = classify_query(question, has_document=False)

    sources = None
    verified = None
    history_key = f"{session_id}_{document_id or 'no_document'}"
    history_text = format_history(get_history(history_key))
    search_q = question
    if needs_rewrite(question, history_text):
        from app.services.llm import rewrite_followup
        search_q = rewrite_followup(question, history_text)

    if route == "pdf":
        answer, sources, context = ask_with_resources(search_q, document_id)
    elif route == "web":
        answer = answer_web(question)
    else:
        answer = answer_general(question, history_text)

    add_to_history(history_key, question, answer)

    return {
        "question": question,
        "document_id": document_id,
        "mode": mode,
        "answered_using": route,
        "answer": answer,
        "sources": sources,
        "verified": verified
    }