"""AI Agent 1 - Government Scheme Advisor.

Analyses a citizen profile, retrieves relevant chunks from the RAG knowledge
base, and recommends eligible schemes with explanations. All scheme facts come
strictly from the retrieved documents.
"""
from __future__ import annotations

from agents.common import NO_INFO_MESSAGE, extract_json, profile_summary
from models.schemas import RecommendationResponse, SchemeRecommendation
from services.llm_service import get_llm
from services.rag_service import rag_service

SYSTEM_PROMPT = (
    "You are a Government Welfare Scheme Advisor for citizens of India. "
    "You must ONLY use the information contained in the provided context, which "
    "comes from official government scheme documents. Never invent schemes, "
    "eligibility rules, benefits, documents, processes, or websites. If the "
    "context does not contain enough information to recommend schemes for this "
    "person, return an empty recommendations array."
)

USER_PROMPT_TEMPLATE = """Citizen profile:
{profile}

Context from government scheme documents:
{context}

Based ONLY on the context above, identify the government welfare schemes this
citizen is currently eligible for. Respond with STRICT JSON in exactly this shape:

{{
  "recommendations": [
    {{
      "name": "scheme name",
      "why_eligible": "why this citizen qualifies, referencing their profile",
      "benefits": "the benefits described in the documents",
      "required_documents": ["document 1", "document 2"],
      "application_process": "how to apply, per the documents",
      "official_website": "official URL if present in the documents, else null"
    }}
  ]
}}

Only include schemes supported by the context. Do not add commentary outside the JSON."""


def recommend_schemes(profile: dict) -> RecommendationResponse:
    summary = profile_summary(profile)

    if not rag_service.has_documents():
        return RecommendationResponse(
            recommendations=[],
            sources=[],
            message=NO_INFO_MESSAGE,
        )

    # Build a retrieval query from the profile.
    query = (
        f"government welfare schemes eligibility for {profile.get('occupation')} "
        f"{profile.get('category')} category age {profile.get('age')} "
        f"income {profile.get('annual_income')} state {profile.get('state')}"
    )
    context, sources = rag_service.build_context(query)

    if not context.strip():
        return RecommendationResponse(
            recommendations=[], sources=[], message=NO_INFO_MESSAGE
        )

    llm = get_llm()
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT_TEMPLATE.format(profile=summary, context=context)),
    ]
    result = llm.invoke(messages)
    data = extract_json(result.content if hasattr(result, "content") else str(result))

    recommendations: list[SchemeRecommendation] = []
    if isinstance(data, dict):
        for item in data.get("recommendations", []) or []:
            try:
                recommendations.append(SchemeRecommendation(**item))
            except Exception:
                continue

    message = None if recommendations else NO_INFO_MESSAGE
    return RecommendationResponse(
        recommendations=recommendations, sources=sources, message=message
    )
