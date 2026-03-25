"""
RAG pipeline: retrieval + Gemini answer generation.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from vectorstore import search

# Load API key from ../.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_best_model():
    """Dynamically find an available Gemini model."""
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prefer flash for speed/cost, then pro
        for model_name in ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro", "models/gemini-1.0-pro"]:
            if model_name in available_models:
                return model_name
        # Fallback to the first available if none of our preferred ones are found
        if available_models:
            return available_models[0]
    except Exception as e:
        print(f"DEBUG: Error listing models: {e}")
    # Default fallback
    return "gemini-1.5-flash"

SYSTEM_PROMPT = """You are a company policy assistant. You answer employee questions ONLY based on the provided policy context below. Follow these rules strictly:

1. Answer ONLY from the provided context. Do not use any external knowledge.
2. If the answer is not found in the context, say: "I could not find an answer to this question in the company policy documents."
3. Keep your answer concise, professional, and clear.
4. Always reference which document and page the information comes from.
5. Do not guess or invent policy details.
"""


def build_context(results: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    if not results:
        return "No relevant policy sections were found."

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[Source {i}: {r['filename']}, Page {r['page']}]\n{r['text']}"
        )
    return "\n\n---\n\n".join(parts)


def ask(question: str, top_k: int = 3) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks
    2. Build context
    3. Query Gemini for a grounded answer
    Returns dict with answer, sources
    """
    # Retrieve
    results = search(question, top_k=top_k)

    if not results:
        return {
            "answer": "No policy documents have been indexed yet. Please upload documents through the Admin page first.",
            "sources": [],
        }

    # Build context
    context = build_context(results)

    # Build prompt
    user_prompt = f"""Context from company policy documents:

{context}

---

Employee Question: {question}

Provide a clear, grounded answer based ONLY on the above context. Reference the source document and page number in your answer."""

    # Call Gemini (Consolidated and Optimized)
    try:
        # Dynamically select model to avoid 404/quota errors on specific versions
        model_name = get_best_model()
        model = genai.GenerativeModel(model_name)
        
        # Build prompt: Context + Question
        full_prompt = f"{SYSTEM_PROMPT}\n\nContext from company policy documents:\n{context}\n\nEmployee Question: {question}"
        
        response = model.generate_content(full_prompt)
        
        # Format sources for frontend
        sources = [
            {"filename": r["filename"], "page": r["page"], "text": r["text"][:150] + "...", "score": r["score"]}
            for r in results
        ]

        if not response or not hasattr(response, 'text'):
            return {
                "answer": "I received an empty or blocked response from the AI model. This usually happens when the safety filter is triggered or the API quota is reached.",
                "sources": sources,
            }
            
        answer = response.text
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return a partial result if retrieval worked but generation failed
        sources = [
            {"filename": r["filename"], "page": r["page"], "text": r["text"][:150] + "...", "score": r["score"]}
            for r in results
        ]
        return {
            "answer": f"API Error: {str(e)}. Please wait a moment or check your Gemini API quota.",
            "sources": sources,
        }

    return {
        "answer": answer,
        "sources": sources,
    }
