from __future__ import annotations

from dataclasses import dataclass

from src.models import SearchResult
from src.oci_client import OCIChatClient
from src.prompts import NO_CONTEXT_MESSAGE, SYSTEM_INSTRUCTIONS, build_user_prompt
from src.retriever import BM25Retriever
from src.safety import evaluate_question


@dataclass(frozen=True, slots=True)
class AgentResponse:
    answer: str
    sources: tuple[SearchResult, ...]
    response_type: str
    used_oci: bool
    model_id: str | None = None


class ClinIAAgent:
    """Orquesta seguridad, recuperación documental y generación con OCI."""

    def __init__(
        self,
        retriever: BM25Retriever,
        oci_client: OCIChatClient,
        *,
        top_k: int = 4,
    ) -> None:
        self.retriever = retriever
        self.oci_client = oci_client
        self.top_k = top_k

    @staticmethod
    def _is_no_context_answer(answer: str) -> bool:
        normalized = " ".join(answer.lower().split())
        expected = " ".join(NO_CONTEXT_MESSAGE.lower().split())
        return expected in normalized

    def answer(self, question: str) -> AgentResponse:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("La pregunta no puede estar vacía")

        safety = evaluate_question(clean_question)
        if safety.blocked:
            return AgentResponse(
                answer=safety.response or "Consulta fuera del alcance administrativo.",
                sources=(),
                response_type=safety.category or "blocked",
                used_oci=False,
            )

        results = self.retriever.search(clean_question, top_k=self.top_k)
        if not results:
            return AgentResponse(
                answer=NO_CONTEXT_MESSAGE,
                sources=(),
                response_type="no_context",
                used_oci=False,
            )

        prompt = build_user_prompt(clean_question, results)
        generated = self.oci_client.chat(
            system_prompt=SYSTEM_INSTRUCTIONS,
            user_prompt=prompt,
        )

        if self._is_no_context_answer(generated.text):
            return AgentResponse(
                answer=NO_CONTEXT_MESSAGE,
                sources=(),
                response_type="no_context",
                used_oci=True,
                model_id=generated.model_id,
            )

        return AgentResponse(
            answer=generated.text.strip(),
            sources=tuple(results),
            response_type="grounded_answer",
            used_oci=True,
            model_id=generated.model_id,
        )
