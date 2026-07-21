from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    blocked: bool
    response: str | None = None
    category: str | None = None


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


EMERGENCY_PATTERNS = [
    r"dolor (fuerte )?en el pecho",
    r"no puedo respirar",
    r"dificultad para respirar",
    r"me falta el aire",
    r"convulsion",
    r"perdi(o|ó) el conocimiento",
    r"sangrado abundante",
    r"intento de suicidio",
    r"quiero suicidarme",
]

MEDICAL_ADVICE_PATTERNS = [
    r"que medicamento",
    r"que remedio",
    r"que puedo tomar",
    r"que dosis",
    r"diagnostica",
    r"diagnostico",
    r"que enfermedad tengo",
    r"interpreta(r)? (mis )?sintomas",
    r"debo suspender",
]


def evaluate_question(question: str) -> SafetyDecision:
    """Bloquea consultas clínicas que exceden el alcance administrativo."""

    normalized = _normalize(question)

    if any(re.search(pattern, normalized) for pattern in EMERGENCY_PATTERNS):
        return SafetyDecision(
            blocked=True,
            category="emergency",
            response=(
                "No puedo evaluar una emergencia médica. Buscá atención inmediata en un "
                "servicio de urgencias o comunicate con el número local de emergencias."
            ),
        )

    if any(re.search(pattern, normalized) for pattern in MEDICAL_ADVICE_PATTERNS):
        return SafetyDecision(
            blocked=True,
            category="medical_advice",
            response=(
                "ClinIA brinda información administrativa. No puede diagnosticar, interpretar "
                "síntomas ni recomendar medicamentos. Consultá con un profesional de salud."
            ),
        )

    return SafetyDecision(blocked=False)
