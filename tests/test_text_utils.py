import pytest

from src.text_utils import normalize_text, split_text


def test_normalize_text_removes_extra_spaces() -> None:
    assert normalize_text("Hola    mundo\n\n\nPrueba") == "Hola mundo\n\nPrueba"


def test_split_text_creates_overlapping_chunks() -> None:
    text = " ".join(f"palabra{i}" for i in range(300))
    chunks = split_text(text, chunk_size=200, overlap=40)

    assert len(chunks) > 2
    assert all(chunk for chunk in chunks)
    assert all(len(chunk) <= 205 for chunk in chunks)


def test_split_text_validates_parameters() -> None:
    with pytest.raises(ValueError):
        split_text("texto", chunk_size=100, overlap=100)
