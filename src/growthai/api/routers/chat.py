"""AI health-assistant route (feature #8)."""

from __future__ import annotations

from fastapi import APIRouter

from growthai.api.schemas import ChatRequest, ChatResponseOut
from growthai.chatbot.providers import get_chat_provider

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("", response_model=ChatResponseOut, summary="Ask the WHO-grounded health assistant")
def ask(req: ChatRequest) -> ChatResponseOut:
    response = get_chat_provider().ask(req.question)
    return ChatResponseOut(**response.as_dict())
