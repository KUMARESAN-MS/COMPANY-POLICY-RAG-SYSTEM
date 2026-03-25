"""
Document loader and text chunking utilities.
Supports PDF and DOCX file formats.
"""

import re
from PyPDF2 import PdfReader
from docx import Document


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text from a PDF file, returning a list of {page, text} dicts."""
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    return pages


def extract_text_from_docx(file_path: str) -> list[dict]:
    """Extract text from a DOCX file, returning a list of {page, text} dicts."""
    doc = Document(file_path)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    # DOCX doesn't have page numbers inherently; treat as single page
    if full_text.strip():
        return [{"page": 1, "text": full_text.strip()}]
    return []


def extract_text(file_path: str) -> list[dict]:
    """Detect file type and extract text."""
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


def clean_text(text: str) -> str:
    """Basic text cleaning."""
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def chunk_text(
    pages: list[dict],
    chunk_size: int = 1500,  # rough char limit per chunk
    chunk_overlap: int = 200, # char overlap
) -> list[dict]:
    """
    Split extracted pages into overlapping chunks by sentences to maintain context.
    Each chunk dict has: text, page, chunk_id
    """
    import re
    chunks = []
    chunk_id = 0

    for page_data in pages:
        page_num = page_data["page"]
        text = clean_text(page_data["text"])
        
        # Split into sentences using punctuation (. ! ?) followed by whitespace
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        start = 0
        while start < len(sentences):
            current_sentences = []
            current_length = 0
            end = start
            
            # Build forward
            while end < len(sentences):
                s = sentences[end]
                s_len = len(s)
                if current_length == 0 or current_length + s_len <= chunk_size:
                    current_sentences.append(s)
                    current_length += s_len + 1 # +1 for space
                    end += 1
                else:
                    break
            
            chunks.append({
                "chunk_id": chunk_id,
                "page": page_num,
                "text": " ".join(current_sentences),
            })
            chunk_id += 1
            
            if end == len(sentences):
                break
                
            # Backtrack for overlap
            backtrack = end - 1
            overlap_length = 0
            while backtrack > start:
                s_len = len(sentences[backtrack])
                if overlap_length + s_len <= chunk_overlap:
                    overlap_length += s_len + 1
                    backtrack -= 1
                else:
                    break
            
            start = backtrack + 1

    return chunks
