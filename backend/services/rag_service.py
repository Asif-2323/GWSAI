"""RAG pipeline: load PDFs from backend/rag/, chunk, embed, store in ChromaDB.

No scheme data is hardcoded. Every document, chunk and embedding originates
from the PDF files the user places inside ``backend/rag/`` (recursively).
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from config import settings

logger = logging.getLogger("rag")


class RagService:
    """Manages the vector store lifecycle and retrieval."""

    def __init__(self) -> None:
        self._vectorstore = None
        self._lock = threading.Lock()
        self._documents_indexed = 0
        self._chunks_indexed = 0

    # -- internal helpers --------------------------------------------------
    def _get_vectorstore(self):
        if self._vectorstore is not None:
            return self._vectorstore
        from langchain_chroma import Chroma

        from services.embedding_service import get_embeddings

        settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
        self._vectorstore = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=get_embeddings(),
            persist_directory=str(settings.vector_db_dir),
        )
        return self._vectorstore

    def _discover_pdfs(self) -> list[Path]:
        docs_dir = settings.rag_docs_dir
        if not docs_dir.exists():
            return []
        return sorted(docs_dir.rglob("*.pdf"))

    # -- public API --------------------------------------------------------
    def ingest(self, force: bool = False) -> dict:
        """Read every PDF under backend/rag/, split, embed and store.

        Safe to call on an empty folder: it simply indexes nothing.
        """
        with self._lock:
            pdfs = self._discover_pdfs()
            store = self._get_vectorstore()

            existing = 0
            try:
                existing = store._collection.count()
            except Exception:  # pragma: no cover - defensive
                existing = 0

            # A forced reindex must rebuild from the files currently on disk.
            # Adding documents to the existing collection would leave stale
            # chunks behind and duplicate chunks from PDFs already indexed.
            if force:
                logger.info("Clearing existing RAG collection before reindexing.")
                store.delete_collection()
                self._vectorstore = None
                store = self._get_vectorstore()
                existing = 0

            if existing > 0 and not force:
                self._chunks_indexed = existing
                self._documents_indexed = len({m.get("source") for m in
                                               self._all_sources()})
                return self.status()

            if not pdfs:
                self._documents_indexed = 0
                self._chunks_indexed = existing
                return self.status()

            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )

            all_chunks = []
            indexed_documents = 0
            for pdf in pdfs:
                try:
                    pages = PyPDFLoader(str(pdf)).load()
                    if not any(page.page_content.strip() for page in pages):
                        logger.warning(
                            "Skipping %s: the PDF contains no extractable text. "
                            "Run OCR or export it again as a text-based PDF.",
                            pdf.name,
                        )
                        continue
                    for page in pages:
                        page.metadata["source"] = pdf.name
                        page.metadata["path"] = str(pdf.relative_to(settings.rag_docs_dir))
                    all_chunks.extend(splitter.split_documents(pages))
                    indexed_documents += 1
                except Exception as exc:  # pragma: no cover
                    logger.warning("Failed to load %s: %s", pdf, exc)

            if all_chunks:
                store.add_documents(all_chunks)

            self._documents_indexed = indexed_documents
            self._chunks_indexed = len(all_chunks)
            logger.info(
                "RAG ingest complete: %d PDFs, %d chunks",
                self._documents_indexed,
                self._chunks_indexed,
            )
            return self.status()

    def _all_sources(self) -> list[dict]:
        try:
            store = self._get_vectorstore()
            data = store._collection.get(include=["metadatas"])
            return data.get("metadatas") or []
        except Exception:  # pragma: no cover
            return []

    def retrieve(self, query: str, k: int | None = None):
        """Return the most relevant chunks for a query."""
        store = self._get_vectorstore()
        try:
            count = store._collection.count()
        except Exception:
            count = 0
        if count == 0:
            return []
        return store.similarity_search(query, k=k or settings.retrieval_k)

    def chunk_count(self) -> int:
        """Return the number of currently indexed chunks."""
        try:
            return self._get_vectorstore()._collection.count()
        except Exception:
            return 0

    def build_context(self, query: str, k: int | None = None) -> tuple[str, list[str]]:
        """Return a joined context string and the list of source filenames."""
        docs = self.retrieve(query, k=k)
        context_parts: list[str] = []
        sources: list[str] = []
        for doc in docs:
            src = doc.metadata.get("source", "unknown")
            context_parts.append(f"[Source: {src}]\n{doc.page_content}")
            if src not in sources:
                sources.append(src)
        return "\n\n---\n\n".join(context_parts), sources

    def has_documents(self) -> bool:
        try:
            return self._get_vectorstore()._collection.count() > 0
        except Exception:
            return False

    def status(self) -> dict:
        ready = self.has_documents()
        return {
            "documents_indexed": self._documents_indexed,
            "chunks_indexed": self._chunks_indexed,
            "embedding_model": settings.embedding_model,
            "collection": settings.chroma_collection,
            "ready": ready,
            "message": (
                "Knowledge base ready."
                if ready
                else "No PDFs found in backend/rag/. Add scheme documents to enable answers."
            ),
        }


rag_service = RagService()
