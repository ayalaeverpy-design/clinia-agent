from __future__ import annotations

import re
from dataclasses import dataclass

from src.models import SearchResult
from src.oci_client import OCIChatClient
from src.prompts import (
    NO_CONTEXT_MESSAGE,
    SYSTEM_INSTRUCTIONS,
    build_repair_prompt,
    build_user_prompt,
)
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

    _TRAILING_CONNECTORS = {
        "a",
        "al",
        "con",
        "de",
        "del",
        "el",
        "en",
        "e",
        "la",
        "las",
        "los",
        "o",
        "para",
        "por",
        "que",
        "se",
        "sin",
        "su",
        "sus",
        "un",
        "una",
        "y",
    }

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

    @classmethod
    def _looks_incomplete(cls, answer: str) -> bool:
        """Detecta respuestas que terminan sin cerrar la idea."""

        text = answer.strip()
        if not text:
            return True

        # Una respuesta normal debe terminar en puntuación de cierre.
        if text[-1] not in ".!?)]}»”":
            return True

        # También detectamos conectores sueltos antes de la puntuación.
        words = re.findall(r"[a-záéíóúüñ]+", text.lower())
        return bool(words and words[-1] in cls._TRAILING_CONNECTORS)

    @staticmethod
    def _keep_only_complete_sentences(answer: str) -> str:
        """Descarta un fragmento final cortado conservando frases completas."""

        text = " ".join(answer.strip().split())
        if not text:
            return text

        matches = list(re.finditer(r"[.!?](?=\s|$)", text))
        if not matches:
            return text.rstrip(" ,;:-") + "."

        complete = text[: matches[-1].end()].strip()
        return complete or text.rstrip(" ,;:-") + "."

    def _generate_complete_answer(
        self,
        *,
        question: str,
        results: list[SearchResult],
    ):
        prompt = build_user_prompt(question, results)
        generated = self.oci_client.chat(
            system_prompt=SYSTEM_INSTRUCTIONS,
            user_prompt=prompt,
        )

        if not self._looks_incomplete(generated.text):
            return generated

        repaired = self.oci_client.chat(
            system_prompt=SYSTEM_INSTRUCTIONS,
            user_prompt=build_repair_prompt(
                question=question,
                results=results,
                incomplete_answer=generated.text,
            ),
        )

        if self._looks_incomplete(repaired.text):
            # Último respaldo: nunca mostramos al usuario un fragmento cortado.
            repaired = type(repaired)(
                text=self._keep_only_complete_sentences(repaired.text),
                model_id=repaired.model_id,
                finish_reason=repaired.finish_reason,
            )

        return repaired

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

        generated = self._generate_complete_answer(
            question=clean_question,
            results=results,
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
