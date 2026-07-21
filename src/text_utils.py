from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """Normaliza espacios sin eliminar acentos ni signos útiles."""

    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Divide texto por longitud, intentando cortar en límites naturales.

    Esta implementación es deliberadamente simple para el primer prototipo.
    En la siguiente etapa podrá reemplazarse por un separador de LangChain.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap debe ser mayor o igual a 0 y menor que chunk_size")

    cleaned = normalize_text(text)
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        provisional_end = min(start + chunk_size, len(cleaned))
        end = provisional_end

        if provisional_end < len(cleaned):
            search_start = start + max(chunk_size // 2, 1)
            candidates = [
                cleaned.rfind("\n\n", search_start, provisional_end),
                cleaned.rfind(". ", search_start, provisional_end),
                cleaned.rfind("; ", search_start, provisional_end),
                cleaned.rfind(" ", search_start, provisional_end),
            ]
            best = max(candidates)
            if best > start:
                end = best + (2 if cleaned[best : best + 2] in {". ", "; "} else 0)

        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned):
            break
        next_start = max(end - overlap, start + 1)
        start = next_start

    return chunks
