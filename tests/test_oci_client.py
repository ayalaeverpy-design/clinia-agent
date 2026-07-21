from types import SimpleNamespace

from src.oci_client import OCIChatClient, OCIInferenceError


def test_combine_prompts_includes_both_parts() -> None:
    result = OCIChatClient._combine_prompts(
        "No inventes información.",
        "¿Cuál es el horario?",
    )
    assert "No inventes información." in result
    assert "¿Cuál es el horario?" in result
    assert "INSTRUCCIONES OBLIGATORIAS" in result


def test_extract_text_from_generic_response() -> None:
    data = SimpleNamespace(
        chat_response=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=[SimpleNamespace(text="Respuesta correcta")],
                        refusal=None,
                    ),
                    finish_reason="STOP",
                )
            ]
        )
    )
    text, finish_reason = OCIChatClient._extract_text(data)
    assert text == "Respuesta correcta"
    assert finish_reason == "STOP"


def test_extract_text_rejects_empty_choices() -> None:
    data = SimpleNamespace(chat_response=SimpleNamespace(choices=[]))
    try:
        OCIChatClient._extract_text(data)
    except OCIInferenceError as exc:
        assert "sin opciones" in str(exc)
    else:
        raise AssertionError("Se esperaba OCIInferenceError")
