"""
FastAPI Main Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from config.settings import settings
from config.logging import logger
from backend.database.session import init_db
from backend.api.health import router as health_router
from backend.api.incidents import router as incidents_router
from backend.api.ingestion import router as ingestion_router
from backend.api.reports import router as reports_router
from backend.api.review import router as review_router
from backend.api.evaluation import router as evaluation_router
from backend.api.ml_models import router as ml_models_router
from backend.api.chat import router as chat_router
from backend.rag.retriever import KnowledgeRetriever

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Incident Narrative Synthesis — Enterprise Multi-Agent Incident Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(ingestion_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(review_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)
app.include_router(ml_models_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

# Initialize Database and RAG on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Initializing and indexing Knowledge Base RAG documents...")
    kb = KnowledgeRetriever.get_instance()
    logger.info(f"Knowledge Base ready with {len(kb.retriever.chunks)} indexed chunks.")

from fastapi.responses import FileResponse

# Mount static frontend assets
frontend_public = Path(__file__).resolve().parent.parent / "frontend" / "public"
if frontend_public.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_public)), name="static")

# Dedicated MNC Enterprise Multi-Page Routes
PAGE_FILES = {
    "index": "index.html",
    "timeline": "timeline.html",
    "rca": "rca.html",
    "aiops-ml": "aiops-ml.html",
    "topology": "topology.html",
    "logs": "logs.html",
    "privacy": "privacy.html",
    "report": "report.html",
    "benchmarks": "benchmarks.html",
    "forensic-matrix": "forensic-matrix.html",
    "interactive-timeline": "interactive-timeline.html",
    "radar": "radar.html",
    "causal-graph": "causal-graph.html",
    "gis-damage": "gis-damage.html",
}

def make_page_handler(filename: str):
    def page_handler():
        page_path = frontend_public / filename
        if page_path.exists():
            return FileResponse(page_path)
        return FileResponse(frontend_public / "index.html")
    return page_handler

for route_name, file_name in PAGE_FILES.items():
    app.get(f"/{route_name}", include_in_schema=False)(make_page_handler(file_name))
    app.get(f"/{file_name}", include_in_schema=False)(make_page_handler(file_name))

@app.get("/")
def serve_dashboard():
    index_file = frontend_public / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "platform": settings.PROJECT_NAME,
        "status": "operational",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
