"""AI Agent 2 - Future Welfare Roadmap Generator.

Projects how a citizen's eligibility evolves over time (age, income, occupation
changes) and produces a staged roadmap. Grounded strictly in the RAG documents.
"""
from __future__ import annotations

from agents.common import NO_INFO_MESSAGE, extract_json, profile_summary
from models.schemas import RoadmapMilestone, RoadmapResponse
from services.llm_service import get_llm
from services.rag_service import rag_service

SYSTEM_PROMPT = (
    "You are a Future Welfare Roadmap planner for citizens of India. Using ONLY "
    "the provided context from official scheme documents, project which schemes a "
    "citizen is eligible for now and which they may become eligible for later as "
    "their age, income, education or occupation changes. Never invent schemes or "
    "rules that are not in the context."
)

USER_PROMPT_TEMPLATE = """Citizen profile:
{profile}

Context from government scheme documents:
{context}

Produce a future eligibility roadmap grounded ONLY in the context. Respond with
STRICT JSON in exactly this shape:

{{
  "milestones": [
    {{
      "stage": "Eligible Now",
      "schemes": ["scheme name", "..."],
      "reasoning": "why these apply at this stage"
    }},
    {{
      "stage": "Age 25",
      "schemes": ["scheme name"],
      "reasoning": "why this scheme becomes applicable"
    }}
  ]
}}

Order milestones chronologically starting with "Eligible Now". Only reference
schemes supported by the context. Do not add commentary outside the JSON."""


def generate_roadmap(profile: dict) -> RoadmapResponse:
    summary = profile_summary(profile)

    if not rag_service.has_documents():
        return RoadmapResponse(milestones=[], sources=[], message=NO_INFO_MESSAGE)

    query = (
        f"welfare schemes by age income category life stage eligibility "
        f"{profile.get('occupation')} {profile.get('category')} {profile.get('state')} "
        f"pension scholarship startup senior citizen"
    )
    context, sources = rag_service.build_context(query)

    if not context.strip():
        return RoadmapResponse(milestones=[], sources=[], message=NO_INFO_MESSAGE)

    llm = get_llm()
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT_TEMPLATE.format(profile=summary, context=context)),
    ]
    result = llm.invoke(messages)
    data = extract_json(result.content if hasattr(result, "content") else str(result))

    milestones: list[RoadmapMilestone] = []
    if isinstance(data, dict):
        for item in data.get("milestones", []) or []:
            try:
                milestones.append(RoadmapMilestone(**item))
            except Exception:
                continue

    message = None if milestones else NO_INFO_MESSAGE
    return RoadmapResponse(milestones=milestones, sources=sources, message=message)
