"""Offline Retrieval-Augmented Generation over the WHO knowledge base.

Uses TF-IDF + cosine similarity (scikit-learn) rather than a hosted embedding
model, so the assistant works with **zero API keys** and no network — ideal for
a portfolio demo a recruiter can run instantly. The knowledge base is chunked by
Markdown ``##`` headings; each heading + body is one retrievable passage.

This is a real, if lightweight, RAG pipeline: retrieve -> ground -> answer. The
answer is composed from the retrieved passages (extractive), and a pluggable LLM
layer (see :mod:`growthai.chatbot.providers`) can replace the composer when a
hosted model is configured.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from growthai.logging_conf import get_logger

logger = get_logger("chatbot.rag")

_KB_PATH = Path(__file__).parent / "knowledge" / "who_guidelines.md"
_SIM_THRESHOLD = 0.06  # below this we admit we don't know


@dataclass(frozen=True, slots=True)
class Passage:
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class RetrievedAnswer:
    answer: str
    sources: list[str]
    confidence: float


def _load_passages(path: Path = _KB_PATH) -> list[Passage]:
    raw = path.read_text(encoding="utf-8")
    passages: list[Passage] = []
    # Split on level-2 headings; keep the heading as the title.
    for block in re.split(r"\n##\s+", raw):
        block = block.strip()
        if not block or block.startswith("#"):
            # Skip the top-level title block.
            if "\n" not in block:
                continue
        lines = block.splitlines()
        title = lines[0].lstrip("# ").strip()
        body = " ".join(line.strip() for line in lines[1:] if line.strip())
        if body:
            passages.append(Passage(title=title, text=body))
    return passages


class KnowledgeBase:
    """In-memory TF-IDF index over the guideline passages."""

    def __init__(self, path: Path = _KB_PATH):
        self.passages = _load_passages(path)
        corpus = [f"{p.title}. {p.text}" for p in self.passages]
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._matrix = self._vectorizer.fit_transform(corpus)
        logger.info("Knowledge base indexed: %d passages", len(self.passages))

    def retrieve(self, query: str, k: int = 3) -> list[tuple[Passage, float]]:
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix).ravel()
        ranked = sims.argsort()[::-1][:k]
        return [(self.passages[i], float(sims[i])) for i in ranked if sims[i] > 0]

    def answer(self, query: str, k: int = 2) -> RetrievedAnswer:
        hits = self.retrieve(query, k=k)
        if not hits or hits[0][1] < _SIM_THRESHOLD:
            return RetrievedAnswer(
                answer=(
                    "I don't have specific guidance on that yet. For anything "
                    "clinical, please consult a paediatrician. You can ask me about "
                    "BMI, healthy weight, nutrition, height, protein, water, sleep, "
                    "activity, screen time or obesity/underweight risk."
                ),
                sources=[],
                confidence=0.0,
            )
        # Extractive composition from the top passages.
        parts = [hits[0][0].text]
        if len(hits) > 1 and hits[1][1] >= _SIM_THRESHOLD:
            parts.append(hits[1][0].text)
        answer = " ".join(parts)
        answer += "\n\n_Educational guidance only - not a medical diagnosis._"
        return RetrievedAnswer(
            answer=answer,
            sources=[p.title for p, _ in hits if _ >= _SIM_THRESHOLD],
            confidence=round(hits[0][1], 3),
        )


@lru_cache(maxsize=1)
def get_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase()
