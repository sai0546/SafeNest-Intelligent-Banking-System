"""
LangChain tools for semantic support search.
"""

import os

import pandas as pd
from langchain.schema import Document
from langchain.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from utils.tool_parsing import parse_int, parse_optional_text

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TICKETS_PATH = os.path.join(BASE, "data", "support_tickets.csv")
VECTOR_STORE_PATH = os.path.join(BASE, "data", "vector_store")

_vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if os.path.exists(os.path.join(VECTOR_STORE_PATH, "index.faiss")):
        _vector_store = FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        return _vector_store

    df = pd.read_csv(TICKETS_PATH)
    documents = [
        Document(page_content=str(row["issue"]), metadata={"resolution": str(row["resolution"])})
        for _, row in df.iterrows()
    ]

    _vector_store = FAISS.from_documents(documents, embeddings)
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    _vector_store.save_local(VECTOR_STORE_PATH)
    return _vector_store


@tool
def search_support_tickets(query: str, top_k=3) -> dict:
    """Search past support tickets using semantic similarity."""
    try:
        query = parse_optional_text(query)
        top_k = parse_int(top_k, "top_k")
        if not query:
            return {"error": "query is required"}

        vector_store = _get_vector_store()
        results = vector_store.similarity_search_with_score(query, k=top_k)
        matches = []
        for doc, score in results:
            similarity = 1 / (1 + score)
            matches.append(
                {
                    "issue": doc.page_content,
                    "resolution": doc.metadata["resolution"],
                    "similarity_score": round(similarity, 3),
                    "confidence": "High" if similarity > 0.7 else "Medium" if similarity > 0.5 else "Low",
                }
            )

        return {"found_matches": len(matches) > 0, "matches": matches, "best_match": matches[0] if matches else None}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_all_support_categories() -> dict:
    """Return the common support issue categories."""
    return {
        "categories": [
            "duplicate_charges",
            "blocked_transactions",
            "account_access",
            "loan_emi",
            "upi_transfers",
            "password_reset",
            "limit_increase",
            "fraudulent_activity",
        ]
    }


@tool
def escalate_to_human() -> dict:
    """Escalate the case to a human support agent."""
    return {
        "escalated": True,
        "message": "Your query has been forwarded to a support agent. You will receive a callback within 24 hours.",
        "ticket_id": f"TKT-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
    }


SUPPORT_TOOLS = [search_support_tickets, get_all_support_categories, escalate_to_human]
