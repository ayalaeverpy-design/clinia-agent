from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd
from pypdf import PdfReader

from src.models import DocumentRecord
from src.text_utils import normalize_text

SUPPORTED_EXTENSIONS = {".pdf", ".csv"}


def load_pdf(path: Path) -> list[DocumentRecord]:
    """Extrae un registro por página desde un PDF con texto seleccionable."""

    records: list[DocumentRecord] = []
    reader = PdfReader(str(path))

    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if not text:
            continue
        records.append(
            DocumentRecord(
                content=text,
                source=path.name,
                document_type="pdf",
                page=page_number,
            )
        )

    return records


def _stringify(value: object) -> str:
    if pd.isna(value):
        return ""
    return normalize_text(str(value))


def _csv_row_to_text(row: pd.Series) -> str:
    """Convierte una fila CSV en texto fácil de recuperar por un buscador."""

    data = {str(column): _stringify(value) for column, value in row.items()}

    if data.get("pregunta") and data.get("respuesta"):
        parts = []
        if data.get("categoria"):
            parts.append(f"Categoría: {data['categoria']}")
        parts.append(f"Pregunta: {data['pregunta']}")
        parts.append(f"Respuesta: {data['respuesta']}")
        return "\n".join(parts)

    visible_parts = [
        f"{column.replace('_', ' ').capitalize()}: {value}"
        for column, value in data.items()
        if value and column not in {"es_ficticio"}
    ]
    return "\n".join(visible_parts)


def load_csv(path: Path) -> list[DocumentRecord]:
    """Extrae un registro por fila desde un CSV UTF-8."""

    dataframe = pd.read_csv(path, encoding="utf-8")
    records: list[DocumentRecord] = []

    for zero_based_index, row in dataframe.iterrows():
        text = _csv_row_to_text(row)
        if not text:
            continue
        category = _stringify(row.get("categoria", "")) or None
        records.append(
            DocumentRecord(
                content=text,
                source=path.name,
                document_type="csv",
                row=int(zero_based_index) + 2,  # suma cabecera y usa numeración humana
                category=category,
            )
        )

    return records


def iter_supported_files(data_dir: Path) -> Iterable[Path]:
    if not data_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de documentos: {data_dir}")
    if not data_dir.is_dir():
        raise NotADirectoryError(f"La ruta no es una carpeta: {data_dir}")

    return sorted(
        path
        for path in data_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_documents(data_dir: str | Path) -> list[DocumentRecord]:
    """Carga todos los PDF y CSV admitidos desde una carpeta."""

    directory = Path(data_dir)
    records: list[DocumentRecord] = []

    for path in iter_supported_files(directory):
        try:
            if path.suffix.lower() == ".pdf":
                records.extend(load_pdf(path))
            elif path.suffix.lower() == ".csv":
                records.extend(load_csv(path))
        except Exception as exc:  # agrega contexto antes de propagar el error
            raise RuntimeError(f"No se pudo procesar {path.name}: {exc}") from exc

    return records


def document_summary(records: list[DocumentRecord]) -> dict[str, object]:
    """Genera métricas simples para validar la ingesta documental."""

    by_source = Counter(record.source for record in records)
    return {
        "total_records": len(records),
        "total_characters": sum(len(record.content) for record in records),
        "sources": dict(sorted(by_source.items())),
    }
