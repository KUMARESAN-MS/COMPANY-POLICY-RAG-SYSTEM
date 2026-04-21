"""
FAISS vector store and SQLite metadata storage.
Uses sentence-transformers for embedding generation.
"""

import os
import json
import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "policy.index")
METADATA_DB_PATH = os.path.join(DATA_DIR, "metadata.db")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Lazy-loaded globals
_model: SentenceTransformer | None = None
_index: faiss.IndexFlatIP | None = None
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _init_db():
    """Initialize SQLite metadata database."""
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            num_chunks INTEGER DEFAULT 0,
            status TEXT DEFAULT 'indexed'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            page_number INTEGER,
            text TEXT NOT NULL,
            faiss_id INTEGER NOT NULL,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


_init_db()


def get_index() -> faiss.IndexFlatIP:
    """Load or create the FAISS index."""
    global _index
    if _index is not None:
        return _index

    if os.path.exists(FAISS_INDEX_PATH):
        _index = faiss.read_index(FAISS_INDEX_PATH)
    else:
        _index = faiss.IndexFlatIP(EMBEDDING_DIM)
    return _index


def save_index():
    """Persist the FAISS index to disk."""
    idx = get_index()
    faiss.write_index(idx, FAISS_INDEX_PATH)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate normalized embeddings for a list of texts."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype="float32")


def add_document(filename: str, chunks: list[dict]) -> int:
    """
    Add a document's chunks to FAISS and metadata DB.
    Returns the document id.
    """
    from datetime import datetime

    index = get_index()
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()

    # Insert document record
    cur.execute(
        "INSERT INTO documents (filename, upload_time, num_chunks) VALUES (?, ?, ?)",
        (filename, datetime.utcnow().isoformat(), len(chunks)),
    )
    doc_id = cur.lastrowid

    # Embed all chunk texts
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    # Current FAISS index size = starting faiss_id for these chunks
    start_faiss_id = index.ntotal
    index.add(embeddings)

    # Insert chunk records
    for i, chunk in enumerate(chunks):
        cur.execute(
            "INSERT INTO chunks (doc_id, chunk_index, page_number, text, faiss_id) VALUES (?, ?, ?, ?, ?)",
            (doc_id, chunk["chunk_id"], chunk["page"], chunk["text"], start_faiss_id + i),
        )

    conn.commit()
    conn.close()
    save_index()
    return doc_id


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the FAISS index for the most similar chunks to the query.
    Returns list of dicts with text, page, filename, score.
    """
    index = get_index()
    if index.ntotal == 0:
        return []

    query_embedding = embed_texts([query])
    scores, ids = index.search(query_embedding, min(top_k, index.ntotal))

    results = []
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()

    for score, faiss_id in zip(scores[0], ids[0]):
        if faiss_id == -1:
            continue
        cur.execute(
            """
            SELECT c.text, c.page_number, d.filename
            FROM chunks c JOIN documents d ON c.doc_id = d.id
            WHERE c.faiss_id = ?
            """,
            (int(faiss_id),),
        )
        row = cur.fetchone()
        if row:
            results.append({
                "text": row[0],
                "page": row[1],
                "filename": row[2],
                "score": float(score),
            })

    conn.close()
    return results


def get_all_documents() -> list[dict]:
    """Return list of all indexed documents with metadata."""
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, filename, upload_time, num_chunks, status FROM documents ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "filename": r[1], "upload_time": r[2], "num_chunks": r[3], "status": r[4]}
        for r in rows
    ]


def delete_document(doc_id: int) -> bool:
    """Delete a document from metadata DB and rebuild the FAISS index."""
    global _index

    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()

    # Check if document exists
    cur.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
    if not cur.fetchone():
        conn.close()
        return False

    # Delete chunks and document from SQLite
    cur.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()

    # Rebuild FAISS index from remaining chunks
    cur.execute("SELECT id, text FROM chunks ORDER BY id")
    remaining_chunks = cur.fetchall()

    # Create a fresh FAISS index
    _index = faiss.IndexFlatIP(EMBEDDING_DIM)

    if remaining_chunks:
        # Re-embed all remaining chunks
        texts = [row[1] for row in remaining_chunks]
        embeddings = embed_texts(texts)
        _index.add(embeddings)

        # Update faiss_id references in SQLite to match new index positions
        for new_faiss_id, (chunk_id, _) in enumerate(remaining_chunks):
            cur.execute("UPDATE chunks SET faiss_id = ? WHERE id = ?", (new_faiss_id, chunk_id))
        conn.commit()

    conn.close()
    save_index()
    return True
