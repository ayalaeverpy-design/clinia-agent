from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True, slots=True)
class OCISettings:
    """Configuración no sensible de la integración con OCI Generative AI."""

    auth_mode: str
    config_file: Path
    config_profile: str
    compartment_id: str | None
    region: str | None
    model_id: str
    endpoint: str | None
    max_tokens: int
    temperature: float
    top_p: float


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned or "REEMPLAZAR" in cleaned.upper():
        return None
    return cleaned


def _normalize_auth_mode(value: str | None) -> str:
    normalized = (value or "CONFIG_FILE").strip().upper()
    aliases = {
        "CONFIG": "CONFIG_FILE",
        "USER_PRINCIPAL": "CONFIG_FILE",
        "INSTANCE": "INSTANCE_PRINCIPAL",
        "INSTANCE_PRINCIPALS": "INSTANCE_PRINCIPAL",
    }
    normalized = aliases.get(normalized, normalized)

    allowed = {"CONFIG_FILE", "INSTANCE_PRINCIPAL"}
    if normalized not in allowed:
        raise ValueError(
            "OCI_AUTH_MODE debe ser CONFIG_FILE o INSTANCE_PRINCIPAL"
        )
    return normalized


def load_oci_settings() -> OCISettings:
    """Lee la configuración del archivo .env sin exponer credenciales."""

    config_file = Path(
        os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
    ).expanduser()

    return OCISettings(
        auth_mode=_normalize_auth_mode(os.getenv("OCI_AUTH_MODE")),
        config_file=config_file,
        config_profile=os.getenv("OCI_CONFIG_PROFILE", "DEFAULT").strip() or "DEFAULT",
        compartment_id=_clean_optional(os.getenv("OCI_COMPARTMENT_ID")),
        region=_clean_optional(os.getenv("OCI_REGION")),
        model_id=os.getenv(
            "OCI_GENERATIVE_AI_MODEL_ID", "google.gemini-2.5-flash"
        ).strip(),
        endpoint=_clean_optional(os.getenv("OCI_GENERATIVE_AI_ENDPOINT")),
        max_tokens=int(os.getenv("OCI_GENERATIVE_AI_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("OCI_GENERATIVE_AI_TEMPERATURE", "0.15")),
        top_p=float(os.getenv("OCI_GENERATIVE_AI_TOP_P", "0.9")),
    )
