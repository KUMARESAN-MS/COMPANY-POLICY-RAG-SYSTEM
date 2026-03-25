"""
FastAPI backend for RAG-based Company Policy QA System.
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from loader import extract_text, chunk_text
from vectorstore import add_document, get_all_documents, delete_document, get_index
from rag import ask as rag_ask

app = FastAPI(title="Policy QA API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AskRequest(BaseModel):
    question: str
    top_k: int = 3


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]


# ── Upload Endpoint ──────────────────────────────────────────────
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or DOCX policy file, extract, chunk, embed, and index it."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = file.filename.lower().split(".")[-1]
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    # Save file to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Extract text
        pages = extract_text(file_path)
        if not pages:
            raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

        # Chunk text
        chunks = chunk_text(pages)

        # Add to vector store + metadata DB
        doc_id = add_document(file.filename, chunks)

        return {
            "message": f"Document '{file.filename}' indexed successfully.",
            "doc_id": doc_id,
            "num_chunks": len(chunks),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


# ── Ask Endpoint ─────────────────────────────────────────────────
@app.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    """Ask a question against the indexed policy documents."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = rag_ask(req.question, top_k=req.top_k)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


# ── Stats / Documents Endpoint ───────────────────────────────────
@app.get("/documents")
async def list_documents():
    """List all indexed documents."""
    docs = get_all_documents()
    index = get_index()
    return {
        "documents": docs,
        "total_vectors": index.ntotal,
    }


@app.delete("/documents/{doc_id}")
async def remove_document(doc_id: int):
    """Delete a document from the metadata (soft delete)."""
    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document removed from index."}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
