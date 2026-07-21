from src.models import DocumentChunk, SearchResult
from src.prompts import NO_CONTEXT_MESSAGE, SYSTEM_INSTRUCTIONS, build_context, build_user_prompt


def _result() -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            content="La cancelación sin costo requiere 24 horas de anticipación.",
            source="cancelaciones.pdf",
            document_type="pdf",
            chunk_id="c1",
            page=1,
            category="Cancelaciones",
        ),
        score=5.0,
    )


def test_context_contains_source_metadata() -> None:
    context = build_context([_result()])
    assert "cancelaciones.pdf" in context
    assert "página 1" in context
    assert "Cancelaciones" in context


def test_user_prompt_contains_question_and_context() -> None:
    prompt = build_user_prompt("¿Cuándo puedo cancelar?", [_result()])
    assert "¿Cuándo puedo cancelar?" in prompt
    assert "24 horas" in prompt
    assert "ninguna oración" in prompt


def test_system_prompt_requires_complete_answers() -> None:
    assert "No dejes viñetas" in SYSTEM_INSTRUCTIONS
    assert NO_CONTEXT_MESSAGE in SYSTEM_INSTRUCTIONS
