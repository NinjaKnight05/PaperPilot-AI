from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import uuid
from app.services.pdf_processor import extract_text_from_pdf
from app.services.chunker import chunk_documents
from app.services.vector_strore import create_vectors
from dotenv import load_dotenv
load_dotenv()
from app.services.rag_pipeline import create_rag_chain
app = FastAPI(
    title="Advanced PDF RAG",
    version="1.0.0"
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "Advanced PDF RAG is running"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    document_id = str(uuid.uuid4())

    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    content = await file.read()
    file_path.write_bytes(content)

    documents = extract_text_from_pdf(file_path)

    chunks = chunk_documents(documents)

    create_vectors(chunks)


    return {
        "message": "PDF uploaded successfully",
        "document_id": document_id,
        "filename": file.filename,
        "pages" :len(documents),
        "chunks":len(chunks)
    }

@app.post("/ask")
async def ask_questions(question:str):
    rag_chain = create_rag_chain()

    answer = rag_chain.invoke(question)
    return{
        "question":question,
        "answer":answer
    }