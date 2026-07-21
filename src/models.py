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
