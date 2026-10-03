"""Sentence-Transformers embeddings (BAAI/bge-small-en-v1.5) for RAG."""
from __future__ import annotations

from functools import lru_cache

from config import settings


@lru_cache
def get_embeddings():
    """Return a cached HuggingFace embeddings instance.

    The model is downloaded on first use and cached locally. Imported lazily
    to keep backend startup fast and resilient.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
