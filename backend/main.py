"""AI Government Welfare Scheme Advisor - FastAPI application entrypoint.

Route paths are declared WITHOUT the `/api` prefix. On Vercel the prefix is
stripped before requests reach this service, and locally the frontend proxies
`/api/*` here as well.
"""
from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import ai, auth, profile
from config import settings
from database.mongodb import close_mongo_connection, connect_to_mongo
from services.rag_service import rag_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("welfare-advisor")


def _ingest_in_background() -> None:
    """Load and index PDFs from backend/rag/ without blocking startup."""
    try:
        pdf_files = sorted(settings.rag_docs_dir.rglob("*.pdf"))
        logger.info(
            "RAG startup: discovered %d PDF document(s) in %s.",
            len(pdf_files),
            settings.rag_docs_dir,
        )
        # Rebuild at startup so PDFs added or removed since the last run are
        # reflected in Chroma. ``force=True`` safely clears old chunks first.
        status = rag_service.ingest(force=True)
        indexed_documents = status["documents_indexed"]
        indexed_chunks = status["chunks_indexed"]

        if not pdf_files:
            logger.warning(
                "RAG startup: no PDFs found; no scheme documents were indexed. "
                "Add PDFs under %s and reindex.",
                settings.rag_docs_dir,
            )
        elif indexed_documents == len(pdf_files):
            logger.info(
                "RAG indexing confirmed: all %d discovered PDF document(s) are "
                "available in collection '%s' (%d chunk(s)).",
                indexed_documents,
                status["collection"],
                indexed_chunks,
            )
        else:
            logger.warning(
                "RAG indexing incomplete: discovered %d PDF document(s), but the "
                "collection reports %d indexed document(s). Run POST /rag/reindex.",
                len(pdf_files),
                indexed_documents,
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("RAG ingestion skipped: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        logger.info("Connected to MongoDB.")
    except Exception as exc:  # pragma: no cover
        logger.warning("MongoDB connection failed: %s", exc)
    # Rebuild the RAG index on a background thread without delaying API startup.
    threading.Thread(target=_ingest_in_background, daemon=True).start()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Backend API for the AI Government Welfare Scheme Advisor. "
        "Provides JWT auth, citizen profiles, RAG-grounded scheme "
        "recommendations, a future eligibility roadmap, and a chatbot."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(ai.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
