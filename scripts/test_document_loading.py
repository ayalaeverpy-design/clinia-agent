from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.document_loader import document_summary, load_documents


def main() -> int:
    data_dir = PROJECT_ROOT / "data"
    try:
        records = load_documents(data_dir)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    summary = document_summary(records)
    print("Documentos procesados correctamente")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if records:
        first = records[0]
        location = f"página {first.page}" if first.page else f"fila {first.row}"
        print(f"\nPrimer registro: {first.source}, {location}")
        print(first.content[:500])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
