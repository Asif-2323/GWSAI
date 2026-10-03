"""AI endpoints: recommendations (Agent 1), roadmap (Agent 2), chat, RAG status."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from agents.advisor_agent import recommend_schemes
from agents.chat_agent import answer_question
from agents.roadmap_agent import generate_roadmap
from api.profile import record_search
from models.schemas import (
    ChatRequest,
    ChatResponse,
    Profile,
    RagStatus,
    RecommendationResponse,
    RoadmapResponse,
)
from services.llm_service import LLMNotConfiguredError, llm_available
from services.rag_service import rag_service
from utils.deps import get_current_user

router = APIRouter(tags=["ai"])


def _require_llm() -> None:
    if not llm_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI model is not configured. Set AI_GATEWAY_API_KEY on the backend.",
        )


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(
    profile: Profile,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RecommendationResponse:
    _require_llm()
    try:
        result = recommend_schemes(profile.model_dump())
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    await record_search(
        current_user["_id"],
        "recommendation",
        f"Scheme recommendations for {profile.full_name}",
    )
    return result


@router.post("/roadmap", response_model=RoadmapResponse)
async def roadmap(
    profile: Profile,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RoadmapResponse:
    _require_llm()
    try:
        result = generate_roadmap(profile.model_dump())
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    await record_search(
        current_user["_id"],
        "roadmap",
        f"Future roadmap for {profile.full_name}",
    )
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ChatResponse:
    _require_llm()
    try:
        result = answer_question(payload.message, payload.history)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    await record_search(
        current_user["_id"],
        "chat",
        payload.message[:80],
    )
    return result


@router.get("/rag/status", response_model=RagStatus)
async def rag_status() -> RagStatus:
    return RagStatus(**rag_service.status())


@router.post("/rag/reindex", response_model=RagStatus)
async def rag_reindex(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RagStatus:
    """Re-scan backend/rag/ and rebuild the vector store."""
    return RagStatus(**rag_service.ingest(force=True))
