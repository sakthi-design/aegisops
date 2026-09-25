"""
Health Check and System Diagnostics API.
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from config.settings import settings
from backend.rag.retriever import KnowledgeRetriever

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    kb = KnowledgeRetriever.get_instance()
    return {
        "status": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "knowledge_base": {
            "indexed": kb.is_indexed,
            "total_chunks": len(kb.retriever.chunks)
        }
    }
