from pathlib import Path

from src.document_loader import document_summary, load_documents

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_loads_all_expected_sources() -> None:
    records = load_documents(DATA_DIR)
    sources = {record.source for record in records}

    assert sources == {
        "convenios_coberturas.csv",
        "instrucciones_pre_post_consulta.pdf",
        "politica_cancelaciones_reagendamiento.pdf",
        "politica_privacidad_datos_paciente.pdf",
        "preguntas_frecuentes_turnos.csv",
    }


def test_creates_pdf_and_csv_records() -> None:
    records = load_documents(DATA_DIR)

    assert any(record.document_type == "pdf" and record.page for record in records)
    assert any(record.document_type == "csv" and record.row for record in records)
    assert all(record.content.strip() for record in records)


def test_summary_matches_loaded_records() -> None:
    records = load_documents(DATA_DIR)
    summary = document_summary(records)

    assert summary["total_records"] == len(records)
    assert summary["total_characters"] > 1_000
    assert len(summary["sources"]) == 5
