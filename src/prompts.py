from __future__ import annotations

from src.models import SearchResult

SYSTEM_INSTRUCTIONS = """Eres ClinIA, asistente administrativo de la Clínica Vida Plena, una clínica ficticia usada en un proyecto académico.

Reglas obligatorias:
1. Respondé únicamente con la información incluida en el CONTEXTO DOCUMENTAL.
2. No inventes horarios, coberturas, requisitos, precios, políticas ni procedimientos.
3. Si el contexto no alcanza, decí: "No encontré información suficiente en los documentos de la clínica para responder esa consulta. Te recomiendo comunicarte con recepción."
4. No diagnostiques enfermedades, no interpretes síntomas y no recomiendes medicamentos.
5. Usá español claro, tono cordial y respuestas breves.
6. No menciones que sos Gemini ni detalles técnicos del modelo.
7. No agregues una sección de fuentes: la aplicación las mostrará por separado.
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

Redactá la respuesta administrativa usando exclusivamente el contexto anterior."""
