# Employee Explorer (EE)

A RAG-based Company Policy Question Answering System. 

## Structure

- **`backend/`**: FastAPI-based backend that handles document uploading, processing into vector embeddings, and answering queries based on the company policies. It uses FAISS for the vector database and Google Gemini for answering questions.
- **`frontend/`**: React, Vite, and Tailwind CSS frontend with an Ask Policy interface for employees, and a Knowledge Base UI for admins to manage documents.

## Local Development

Ensure your `.env` file is set up with valid API keys before starting the applications. 
_Note: The `.env` file is ignored in version control for security._

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Security & Git
Sensitive paths including `.env`, `backend/uploads/` (uploaded PDFs), and `backend/data/` (local vector database indexing) are deliberately ignored in `.gitignore` to prevent data leakage.
