from __future__ import annotations

from collections import Counter

from src.models import DocumentChunk, DocumentRecord
from src.text_utils import split_text


def create_chunks(
    records: list[DocumentRecord],
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[DocumentChunk]:
    """Convierte registros documentales en fragmentos con metadatos."""

    chunks: list[DocumentChunk] = []

    for record_index, record in enumerate(records, start=1):
        parts = split_text(record.content, chunk_size=chunk_size, overlap=overlap)
        for part_index, content in enumerate(parts, start=1):
            chunks.append(
                DocumentChunk(
                    content=content,
                    source=record.source,
                    document_type=record.document_type,
                    chunk_id=f"doc-{record_index:03d}-chunk-{part_index:03d}",
                    page=record.page,
                    row=record.row,
                    category=record.category,
                )
            )

    return chunks


def chunk_summary(chunks: list[DocumentChunk]) -> dict[str, object]:
    """Devuelve métricas para validar la fragmentación."""

    by_source = Counter(chunk.source for chunk in chunks)
    return {
        "total_chunks": len(chunks),
        "total_characters": sum(len(chunk.content) for chunk in chunks),
        "average_chunk_length": (
            round(sum(len(chunk.content) for chunk in chunks) / len(chunks), 2)
            if chunks
            else 0
        ),
        "sources": dict(sorted(by_source.items())),
    }
