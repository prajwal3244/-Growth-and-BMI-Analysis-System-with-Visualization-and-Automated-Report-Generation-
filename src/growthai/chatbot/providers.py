"""Pluggable chat providers (SOLID: open for extension, closed for modification).

``ChatProvider`` is the interface. ``OfflineRAGProvider`` is the always-available
default. ``OpenAIProvider`` / ``GeminiProvider`` are thin adapters that ground a
hosted LLM with the same retrieved WHO context and only activate when an API key
is configured. Selecting the provider is a one-line config change
(``GROWTHAI_LLM_PROVIDER``), never a code change in callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from growthai.chatbot.rag import get_knowledge_base
from growthai.config import get_settings
from growthai.logging_conf import get_logger

logger = get_logger("chatbot.providers")


@dataclass
class ChatResponse:
    answer: str
    sources: list[str]
    confidence: float
    provider: str

    def as_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "provider": self.provider,
        }


class ChatProvider(ABC):
    """A health-assistant backend."""

    name: str = "base"

    @abstractmethod
    def ask(self, question: str) -> ChatResponse: ...


class OfflineRAGProvider(ChatProvider):
    """Default: pure offline RAG. No API key, always works."""

    name = "offline-rag"

    def ask(self, question: str) -> ChatResponse:
        result = get_knowledge_base().answer(question)
        return ChatResponse(result.answer, result.sources, result.confidence, self.name)


class _LLMGroundedProvider(ChatProvider):
    """Shared logic: retrieve WHO context, then let an LLM phrase the answer."""

    name = "llm"

    def _context(self, question: str) -> tuple[str, list[str], float]:
        hits = get_knowledge_base().retrieve(question, k=3)
        context = "\n".join(f"- {p.text}" for p, _ in hits)
        sources = [p.title for p, s in hits if s > 0]
        conf = hits[0][1] if hits else 0.0
        return context, sources, round(conf, 3)

    def _prompt(self, question: str, context: str) -> str:
        return (
            "You are GrowthAI, a careful paediatric health assistant. Answer the "
            "parent's question using ONLY the WHO/CDC context below. Be warm, concise "
            "and practical. Never diagnose; recommend a paediatrician for clinical "
            f"concerns.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        )

    def _complete(self, prompt: str) -> str:  # pragma: no cover - network
        raise NotImplementedError

    def ask(self, question: str) -> ChatResponse:
        context, sources, conf = self._context(question)
        try:  # pragma: no cover - network path
            answer = self._complete(self._prompt(question, context))
        except Exception as exc:  # noqa: BLE001 - fall back to offline
            logger.warning("LLM provider failed (%s); using offline RAG", exc)
            return OfflineRAGProvider().ask(question)
        return ChatResponse(answer, sources, conf, self.name)


class OpenAIProvider(_LLMGroundedProvider):
    name = "openai"

    def _complete(self, prompt: str) -> str:  # pragma: no cover - network
        from openai import OpenAI

        client = OpenAI(api_key=get_settings().openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""


class GeminiProvider(_LLMGroundedProvider):
    name = "gemini"

    def _complete(self, prompt: str) -> str:  # pragma: no cover - network
        import google.generativeai as genai

        genai.configure(api_key=get_settings().gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(prompt).text or ""


def get_chat_provider() -> ChatProvider:
    """Factory driven by config; safely falls back to offline RAG."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    if provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider()
    if provider not in {"offline", "openai", "gemini"}:
        logger.warning("Unknown LLM provider %r; using offline RAG", provider)
    return OfflineRAGProvider()
