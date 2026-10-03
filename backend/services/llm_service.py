"""Configurable LLM access with a primary provider and OpenRouter fallback.

The application defaults to the configured Gemini-compatible endpoint, but if the
primary provider hits a rate limit or temporary API failure, it quietly retries
with the configured fallback model.
"""
from __future__ import annotations

from functools import lru_cache

from config import settings


class LLMNotConfiguredError(RuntimeError):
    """Raised when no LLM credentials are available."""


class FallbackChatModel:
    """Thin wrapper that retries with a fallback provider when rate-limited."""

    def __init__(self, candidates):
        self._candidates = list(candidates)

    def _is_rate_limited(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "429" in message
            or "rate limit" in message
            or "quota" in message
            or "resource_exhausted" in message
            or "not found" in message
            or "404" in message
            or "unavailable" in message
            or "model is unavailable" in message
        )

    def invoke(self, messages, *args, **kwargs):
        last_error: Exception | None = None

        for model in self._candidates:
            try:
                return model.invoke(messages, *args, **kwargs)
            except Exception as exc:  # pragma: no cover - runtime provider path
                last_error = exc
                if not self._is_rate_limited(exc):
                    raise

        if last_error is not None:
            raise last_error
        raise LLMNotConfiguredError("No valid LLM provider is configured.")

    def __getattr__(self, name):
        return getattr(self._candidates[0], name)


@lru_cache
def get_llm():
    """Return a cached LangChain chat model instance with a configured fallback."""
    from langchain_openai import ChatOpenAI

    candidates = []

    if settings.ai_gateway_api_key:
        candidates.append(
            ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.ai_gateway_api_key,
                base_url=settings.llm_base_url,
            )
        )

    if settings.fallback_ai_gateway_api_key:
        candidates.append(
            ChatOpenAI(
                model=settings.fallback_llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.fallback_ai_gateway_api_key,
                base_url=settings.fallback_llm_base_url,
            )
        )

    if not candidates:
        raise LLMNotConfiguredError(
            "No AI keys are configured. Set AI_GATEWAY_API_KEY and/or FALLBACK_AI_GATEWAY_API_KEY."
        )

    return FallbackChatModel(candidates)


def llm_available() -> bool:
    return bool(settings.ai_gateway_api_key or settings.fallback_ai_gateway_api_key)
