from pathlib import Path

from src.chunking import chunk_summary, create_chunks
from src.document_loader import load_documents

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_create_chunks_preserves_metadata() -> None:
    records = load_documents(DATA_DIR)
    chunks = create_chunks(records, chunk_size=700, overlap=100)

    assert len(chunks) >= len(records)
    assert all(chunk.source for chunk in chunks)
    assert all(chunk.chunk_id for chunk in chunks)
    assert any(chunk.page for chunk in chunks)
    assert any(chunk.row for chunk in chunks)


def test_chunk_summary_returns_metrics() -> None:
    chunks = create_chunks(load_documents(DATA_DIR))
    summary = chunk_summary(chunks)

    assert summary["total_chunks"] == len(chunks)
    assert summary["average_chunk_length"] > 0
    assert len(summary["sources"]) == 5
