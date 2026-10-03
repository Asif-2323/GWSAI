"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Central configuration for the backend service.

    Values are read from environment variables (or a local .env file during
    development). See .env.example for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "AI Government Welfare Scheme Advisor"
    debug: bool = False

    # --- MongoDB ---
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGO_URI", "MONGODB_URI", "mongodb_uri"),
    )
    mongodb_db_name: str = Field(
        default="welfare_advisor",
        validation_alias=AliasChoices("MONGO_DB_NAME", "MONGODB_DB_NAME", "mongodb_db_name"),
    )

    # --- Auth / JWT ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days -> persistent login

    # --- LLM (configurable) ---
    # Primary model for normal requests.
    ai_gateway_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AI_GATEWAY_API_KEY", "ai_gateway_api_key"),
    )
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        validation_alias=AliasChoices("LLM_BASE_URL", "llm_base_url"),
    )
    # Default model. Change LLM_MODEL to switch providers, e.g.:
    #   gemini-3.6-flash
    #   google/gemini-2.0-flash
    #   meta/llama-3.1-70b
    #   alibaba/qwen-2.5-72b
    #   openai/gpt-4o-mini
    llm_model: str = Field(
        default="gemini-3.6-flash",
        validation_alias=AliasChoices("LLM_MODEL", "llm_model"),
    )
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048

    # --- Fallback LLM (OpenRouter) ---
    # Used automatically if the primary model hits rate limits or temporary API errors.
    fallback_ai_gateway_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "FALLBACK_AI_GATEWAY_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENROUTER_KEY",
            "fallback_ai_gateway_api_key",
        ),
    )
    fallback_llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("FALLBACK_LLM_BASE_URL", "fallback_llm_base_url"),
    )
    fallback_llm_model: str = Field(
        default="meta-llama/llama-3.1-8b-instruct",
        validation_alias=AliasChoices("FALLBACK_LLM_MODEL", "fallback_llm_model"),
    )

    # --- RAG / Vector store ---
    rag_docs_dir: Path = BASE_DIR / "rag"
    vector_db_dir: Path = BASE_DIR / "vector_db"
    chroma_collection: str = "welfare_schemes"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    # Normal questions receive the most relevant chunks. Catalogue-style
    # questions (for example, "list all schemes") request the full collection.
    retrieval_k: int = 12

    # --- CORS ---
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
