from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """Unidad de información extraída desde un PDF o CSV."""

    content: str
    source: str
    document_type: str
    page: int | None = None
    row: int | None = None
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """Fragmento recuperable generado a partir de un documento."""

    content: str
    source: str
    document_type: str
    chunk_id: str
    page: int | None = None
    row: int | None = None
    category: str | None = None

    @property
    def location(self) -> str:
        if self.page is not None:
            return f"página {self.page}"
        if self.row is not None:
            return f"fila {self.row}"
        return "ubicación no especificada"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Resultado producido por el recuperador documental."""

    chunk: DocumentChunk
    score: float
