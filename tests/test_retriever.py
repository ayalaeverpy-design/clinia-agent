from pathlib import Path

from src.chunking import create_chunks
from src.document_loader import load_documents
from src.retriever import BM25Retriever, tokenize

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def build_retriever() -> BM25Retriever:
    return BM25Retriever(create_chunks(load_documents(DATA_DIR)))


def test_tokenize_removes_common_stopwords() -> None:
    tokens = tokenize("¿Cómo puedo cancelar el turno de la consulta?")

    assert "el" not in tokens
    assert "cancelar" in tokens
    assert "turno" in tokens


def test_search_finds_cancellation_policy() -> None:
    results = build_retriever().search(
        "¿Con cuánta anticipación puedo cancelar mi turno?",
        top_k=5,
    )

    assert results
    assert any("cancelaciones" in result.chunk.source for result in results[:3])


def test_search_filters_incidental_arrival_match() -> None:
    results = build_retriever().search(
        "¿Con cuánta anticipación puedo cancelar un turno?",
        top_k=5,
    )

    assert results
    labels = [f"{result.chunk.category} {result.chunk.content}".lower() for result in results]
    assert not any("¿con cuánta anticipación debo llegar?" in label for label in labels)


def test_search_finds_privacy_policy() -> None:
    results = build_retriever().search(
        "¿Cómo protege la clínica mis datos personales?",
        top_k=5,
    )

    assert results
    assert any("privacidad" in result.chunk.source for result in results[:3])
