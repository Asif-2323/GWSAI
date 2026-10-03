"""RAG chatbot agent. Answers strictly from the knowledge base, no hallucination."""
from __future__ import annotations

from agents.common import NO_INFO_MESSAGE
from models.schemas import ChatMessage, ChatResponse
from services.llm_service import get_llm
from services.rag_service import rag_service

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about Indian government "
    "welfare schemes. You must answer ONLY using the provided context, which is "
    "retrieved from official government scheme documents. If the answer is not "
    "present in the context, reply with EXACTLY this sentence and nothing else: "
    f'"{NO_INFO_MESSAGE}" '
    "Never use outside knowledge. Be concise, clear and cite scheme names when relevant."
)

USER_PROMPT_TEMPLATE = """Context from government scheme documents:
{context}

Conversation so far:
{history}

User question: {question}

Answer using ONLY the context above."""


def _is_catalogue_request(message: str) -> bool:
    """Return True when the user wants every scheme, not a targeted answer."""
    normalized = " ".join(message.lower().split())
    phrases = (
        "list all schemes",
        "list schemes",
        "all schemes",
        "show all schemes",
        "what schemes are available",
        "which schemes are available",
    )
    return any(phrase in normalized for phrase in phrases)


def answer_question(message: str, history: list[ChatMessage]) -> ChatResponse:
    if not rag_service.has_documents():
        return ChatResponse(answer=NO_INFO_MESSAGE, sources=[])

    # A catalogue request must see every chunk. Normal questions use the
    # configured relevance limit to keep answers focused and efficient.
    context, sources = rag_service.build_context(
        message,
        k=rag_service.chunk_count() if _is_catalogue_request(message) else None,
    )
    if not context.strip():
        return ChatResponse(answer=NO_INFO_MESSAGE, sources=[])

    history_text = "\n".join(
        f"{m.role}: {m.content}" for m in history[-6:]
    ) or "(no previous messages)"

    llm = get_llm()
    messages = [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            USER_PROMPT_TEMPLATE.format(
                context=context, history=history_text, question=message
            ),
        ),
    ]
    result = llm.invoke(messages)
    answer = result.content if hasattr(result, "content") else str(result)
    return ChatResponse(answer=answer.strip(), sources=sources)
