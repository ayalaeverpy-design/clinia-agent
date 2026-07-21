from src.models import DocumentChunk, SearchResult
from src.prompts import build_context, build_user_prompt


def _result() -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            content="La cancelación sin costo requiere 24 horas de anticipación.",
            source="cancelaciones.pdf",
            document_type="pdf",
            chunk_id="abc",
            page=1,
            category="cancelaciones",
        ),
        score=2.5,
    )


def test_context_includes_source_and_location() -> None:
    context = build_context([_result()])
    assert "cancelaciones.pdf" in context
    assert "página 1" in context


def test_user_prompt_includes_question() -> None:
    prompt = build_user_prompt("¿Puedo cancelar?", [_result()])
    assert "¿Puedo cancelar?" in prompt
    assert "CONTEXTO DOCUMENTAL" in prompt
