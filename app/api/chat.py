from fastapi import APIRouter
from typing import Any
import json
import logging

from app.models.schemas import ChatRequest, ChatResponse
from app.core.redis_client import redis_client
from app.core.llm_client import LLMClient
from app.utils.prompt import build_system_prompt

router = APIRouter()
llm = LLMClient()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Endpoint expected payload:
    {
        "session_id": "abc",
        "question": "Which is the cheapest Air India flight after 6 pm?",
        "context": [ { ... flight card objects ... } ]
    }
    """

    # Store context (short TTL) to act as the session's page context
    try:
        await redis_client.set_context(req.session_id, req.context)
    except Exception:
        logging.exception("Failed to set context in Redis — continuing with request")

    system_prompt = build_system_prompt()
    response = await llm.get_response(system_prompt, req.question, req.context)

    # Basic verification: excerpt must be verbatim substring of the stored context
    context_blob = json.dumps(req.context, ensure_ascii=False)

    if response.get("excerpt") and response["excerpt"] in context_blob:
        return ChatResponse(answer=response["answer"], excerpt=response["excerpt"])
    else:
        # safe fallback to avoid hallucinations
        return ChatResponse(answer="I cannot find that information on this page.", excerpt=None)
