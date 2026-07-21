from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from src.models import DocumentChunk, SearchResult

TOKEN_PATTERN = re.compile(r"[a-z0-9áéíóúüñ]+", re.IGNORECASE)

STOPWORDS = {
    "a", "al", "algo", "como", "con", "cual", "cuando", "de", "del", "desde",
    "donde", "el", "ella", "en", "entre", "es", "esta", "este", "esto", "hay",
    "la", "las", "lo", "los", "me", "mi", "mis", "para", "pero", "por", "puedo",
    "que", "se", "si", "sin", "sobre", "su", "sus", "un", "una", "uno", "y", "ya",
}

SYNONYMS = {
    "cita": {"turno"},
    "citas": {"turno"},
    "turnos": {"turno"},
    "cancelar": {"cancelacion", "anular"},
    "cancelo": {"cancelacion"},
    "cancelaciones": {"cancelacion"},
    "reprogramar": {"reagendamiento", "reagendar"},
    "reagendar": {"reagendamiento"},
    "seguro": {"convenio", "cobertura"},
    "aseguradora": {"convenio", "cobertura"},
    "cedula": {"documento", "identidad"},
    "documentos": {"documento", "requisito"},
    "datos": {"privacidad", "informacion"},
    "medicamentos": {"medicacion"},
    "estacionamiento": {"parking", "aparcamiento"},
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def tokenize(text: str, expand_synonyms: bool = False) -> list[str]:
    """Tokeniza texto en español para una recuperación local reproducible."""

    normalized = _strip_accents(text.lower())
    tokens = [token for token in TOKEN_PATTERN.findall(normalized) if token not in STOPWORDS]

    if not expand_synonyms:
        return tokens

    expanded = list(tokens)
    for token in tokens:
        expanded.extend(SYNONYMS.get(token, set()))
    return expanded


def _searchable_text(chunk: DocumentChunk) -> str:
    """Incluye metadatos útiles sin contaminar el contenido mostrado al usuario."""

    return " ".join(
        part
        for part in (
            chunk.category or "",
            chunk.source.replace("_", " ").replace(".", " "),
            chunk.content,
        )
        if part
    )


class BM25Retriever:
    """Índice BM25 liviano con penalización de coincidencias parciales."""

    def __init__(
        self,
        chunks: list[DocumentChunk],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not chunks:
            raise ValueError("Se necesita al menos un fragmento para construir el índice")

        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.document_tokens = [tokenize(_searchable_text(chunk)) for chunk in chunks]
        self.term_frequencies = [Counter(tokens) for tokens in self.document_tokens]
        self.document_lengths = [len(tokens) for tokens in self.document_tokens]
        self.average_document_length = sum(self.document_lengths) / len(self.document_lengths)

        document_frequency: Counter[str] = Counter()
        for tokens in self.document_tokens:
            document_frequency.update(set(tokens))
        self.document_frequency = document_frequency

    def _idf(self, term: str) -> float:
        total_documents = len(self.chunks)
        frequency = self.document_frequency.get(term, 0)
        return math.log(1 + (total_documents - frequency + 0.5) / (frequency + 0.5))

    def _score_document(self, query_tokens: list[str], document_index: int) -> float:
        frequencies = self.term_frequencies[document_index]
        document_length = self.document_lengths[document_index]
        score = 0.0

        for term in query_tokens:
            term_frequency = frequencies.get(term, 0)
            if term_frequency == 0:
                continue

            denominator = term_frequency + self.k1 * (
                1 - self.b + self.b * document_length / self.average_document_length
            )
            score += self._idf(term) * (term_frequency * (self.k1 + 1)) / denominator

        unique_query_terms = set(query_tokens)
        if not unique_query_terms:
            return 0.0

        matched_terms = sum(1 for term in unique_query_terms if frequencies.get(term, 0) > 0)
        coverage = matched_terms / len(unique_query_terms)

        # Un fragmento que coincide con una sola palabra genérica recibe una penalización.
        # Los fragmentos que cubren la intención completa reciben un pequeño refuerzo.
        coverage_factor = 0.5 + coverage**2
        return score * coverage_factor

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        min_score: float = 1.0,
        min_relative_score: float = 0.65,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k debe ser mayor que cero")
        if not 0 <= min_relative_score <= 1:
            raise ValueError("min_relative_score debe estar entre 0 y 1")

        query_tokens = tokenize(query, expand_synonyms=True)
        if not query_tokens:
            return []

        results = [
            SearchResult(chunk=chunk, score=self._score_document(query_tokens, index))
            for index, chunk in enumerate(self.chunks)
        ]
        filtered = [result for result in results if result.score >= min_score]
        filtered.sort(key=lambda result: result.score, reverse=True)

        if not filtered:
            return []

        best_score = filtered[0].score
        relative_cutoff = best_score * min_relative_score
        focused = [result for result in filtered if result.score >= relative_cutoff]
        return focused[:top_k]
