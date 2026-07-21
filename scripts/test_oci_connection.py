from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_oci_settings
from src.oci_client import OCIChatClient


def main() -> None:
    settings = load_oci_settings()
    client = OCIChatClient(settings)
    result = client.chat(
        system_prompt="Respondé exactamente lo solicitado y nada más.",
        user_prompt="Respondé exactamente: CONEXION OCI DESDE PYTHON OK",
    )
    print(result.text)
    print(f"Modelo: {result.model_id}")


if __name__ == "__main__":
    main()
