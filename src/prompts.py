from __future__ import annotations

from src.models import SearchResult

NO_CONTEXT_MESSAGE = (
    "No encontré información suficiente en los documentos de la clínica para responder "
    "esa consulta. Te recomiendo comunicarte con recepción."
)

SYSTEM_INSTRUCTIONS = f"""Eres ClinIA, asistente administrativo de la Clínica Vida Plena, una clínica ficticia usada en un proyecto académico.

Reglas obligatorias:
1. Respondé únicamente con información explícita del CONTEXTO DOCUMENTAL.
2. No inventes horarios, coberturas, requisitos, precios, políticas ni procedimientos.
3. Ignorá fragmentos incidentales que solo compartan una palabra con la pregunta, pero no respondan su intención.
4. Si el contexto no alcanza, respondé exactamente: "{NO_CONTEXT_MESSAGE}"
5. No diagnostiques enfermedades, no interpretes síntomas y no recomiendes medicamentos.
6. Usá español claro, tono cordial y una respuesta breve de hasta 90 palabras.
7. Terminá todas las frases. No dejes viñetas, enumeraciones ni oraciones incompletas.
8. Si usás una lista, incluí como máximo seis puntos y escribí cada punto de forma completa.
9. Toda respuesta debe terminar con punto, signo de interrogación o signo de exclamación.
10. No menciones que sos Gemini ni detalles técnicos del modelo.
11. No agregues una sección de fuentes: la aplicación las mostrará por separado.
"""


def build_context(results: list[SearchResult]) -> str:
    """Convierte resultados recuperados en contexto trazable para el modelo."""

    blocks: list[str] = []
    for position, result in enumerate(results, start=1):
        chunk = result.chunk
        blocks.append(
            "\n".join(
                [
                    f"[FUENTE {position}]",
                    f"Archivo: {chunk.source}",
                    f"Ubicación: {chunk.location}",
                    f"Categoría: {chunk.category or 'sin categoría'}",
                    f"Contenido: {chunk.content}",
                ]
            )
        )
    return "\n\n".join(blocks)


def build_user_prompt(question: str, results: list[SearchResult]) -> str:
    context = build_context(results)
    return f"""CONTEXTO DOCUMENTAL:
{context}

PREGUNTA DEL USUARIO:
{question.strip()}

Redactá una respuesta administrativa completa usando exclusivamente el contexto anterior.
Respondé en hasta 90 palabras. Antes de finalizar, verificá que la última oración termine completamente y con puntuación."""


def build_repair_prompt(
    *,
    question: str,
    results: list[SearchResult],
    incomplete_answer: str,
) -> str:
    context = build_context(results)
    return f"""CONTEXTO DOCUMENTAL:
{context}

PREGUNTA DEL USUARIO:
{question.strip()}

RESPUESTA ANTERIOR INCOMPLETA:
{incomplete_answer.strip()}

Reescribí desde cero una respuesta correcta, completa y breve, usando solo el contexto.
No continúes simplemente desde la última palabra. Usá hasta 80 palabras y terminá con un punto."""
