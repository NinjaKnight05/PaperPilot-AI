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

app = FastAPI(
    title="Advanced PDF RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "Advanced PDF RAG is running"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), session_id: str | None = None):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    if session_id is None:
        session_id = str(uuid.uuid4())

    document_id = str(uuid.uuid4())

    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    content = await file.read()
    file_path.write_bytes(content)

    documents = extract_text_from_pdf(file_path)

    chunks = chunk_documents(documents)
    for chunk in chunks:
        chunk.metadata["document_id"] = document_id

    create_vectors(chunks)

    # Remember this session's document_id (per-session, not shared globally)
    (UPLOAD_DIR / f"session_{session_id}.txt").write_text(document_id)

    return {
        "message": "PDF uploaded successfully",
        "session_id": session_id,
        "document_id": document_id,
        "filename": file.filename,
        "pages": len(documents),
        "chunks": len(chunks)
    }


RECENCY_WORDS = ("latest", "current", "today", "now", "recent", "up to date", "up-to-date")

# Phrases that mean the user is talking about the uploaded document
DOC_WORDS = (
    "this pdf", "the pdf", "my pdf",
    "this document", "the document", "my document",
    "this paper", "the paper",
    "this file", "the file",
)

# Words that mean "give me a general overview"
OVERVIEW_WORDS = ("about", "explain", "summar", "overview", "what is this")

# Used instead of the vague question so retrieval finds the abstract/intro chunks
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
    mode: str = "smart"  # "smart" or "pdf_only"
):
    has_document = False
    session_file = UPLOAD_DIR / f"session_{session_id}.txt"

    if document_id is None and session_file.exists():
        document_id = session_file.read_text().strip()

    if document_id is not None:
        has_document = True

    search_q = question  # what we actually search the PDF with

    if mode == "pdf_only":
        if not has_document:
            raise HTTPException(status_code=400, detail="No document uploaded.")
        route = "pdf"
        if is_overview_question(question):
            search_q = OVERVIEW_QUERY
    else:
        if has_document and is_overview_question(question):
            # "tell me about this pdf", "summarize the document", ...
            route = "pdf"
            search_q = OVERVIEW_QUERY
        elif has_document and mentions_document(question):
            # user clearly means the PDF
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
    else:  # general
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