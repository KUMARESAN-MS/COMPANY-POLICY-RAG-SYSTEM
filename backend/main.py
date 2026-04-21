"""
FastAPI backend for RAG-based Company Policy QA System.
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from loader import extract_text, chunk_text
from vectorstore import add_document, get_all_documents, delete_document, get_index
from rag import ask as rag_ask
from auth import (
    ADMIN_SECRET,
    create_user,
    get_user_by_username,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin,
)

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


# ── Request / Response Models ────────────────────────────────────
class SignupRequest(BaseModel):
    username: str
    password: str
    role: str = "employee"  # "employee" or "admin"
    admin_secret: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    username: str
    role: str


class AskRequest(BaseModel):
    question: str
    top_k: int = 3


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]


# ── Auth Endpoints ───────────────────────────────────────────────
@app.post("/auth/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    """Register a new user. Admin registration requires the admin secret key."""
    if not req.username.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Username and password are required.")

    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    # Validate role
    role = req.role.lower()
    if role not in ("employee", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'employee' or 'admin'.")

    # Admin registration requires secret key
    if role == "admin":
        if not req.admin_secret or req.admin_secret != ADMIN_SECRET:
            raise HTTPException(
                status_code=403,
                detail="Invalid admin secret key. Contact your administrator.",
            )

    # Create user in database
    user = create_user(req.username.strip(), req.password, role)

    # Generate JWT token
    token = create_access_token({"sub": user["username"], "role": user["role"]})

    return {"token": token, "username": user["username"], "role": user["role"]}


@app.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Authenticate a user and return a JWT token."""
    if not req.username.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Username and password are required.")

    user = get_user_by_username(req.username.strip())
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if req.role and req.role.lower() != user["role"].lower():
        raise HTTPException(status_code=401, detail="Incorrect role selected for this account.")

    token = create_access_token({"sub": user["username"], "role": user["role"]})

    return {"token": token, "username": user["username"], "role": user["role"]}


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return {"username": current_user["username"], "role": current_user["role"]}


# ── Upload Endpoint (Admin Only) ────────────────────────────────
@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
):
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


# ── Ask Endpoint (Any Authenticated User) ───────────────────────
@app.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest, current_user: dict = Depends(get_current_user)):
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


# ── Stats / Documents Endpoint (Any Authenticated User) ─────────
@app.get("/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all indexed documents."""
    docs = get_all_documents()
    index = get_index()
    return {
        "documents": docs,
        "total_vectors": index.ntotal,
    }


@app.delete("/documents/{doc_id}")
async def remove_document(doc_id: int, current_user: dict = Depends(require_admin)):
    """Delete a document (Admin only)."""
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
