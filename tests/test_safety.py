from src.safety import evaluate_question


def test_emergency_question_is_blocked() -> None:
    decision = evaluate_question("Tengo dolor fuerte en el pecho, ¿qué hago?")
    assert decision.blocked is True
    assert decision.category == "emergency"


def test_medication_question_is_blocked() -> None:
    decision = evaluate_question("¿Qué medicamento puedo tomar para el dolor?")
    assert decision.blocked is True
    assert decision.category == "medical_advice"


def test_administrative_question_is_allowed() -> None:
    decision = evaluate_question("¿Cómo puedo cancelar mi turno?")
    assert decision.blocked is False
