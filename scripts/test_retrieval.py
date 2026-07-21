from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chunking import create_chunks
from src.document_loader import load_documents
from src.retriever import BM25Retriever

DATA_DIR = PROJECT_ROOT / "data"

questions = [
    "¿Con cuánta anticipación puedo cancelar un turno?",
    "¿Qué documentos tengo que llevar a la consulta?",
    "¿Cómo protege la clínica mis datos personales?",
    "¿Qué cobertura tiene el plan Integral de SaludPlus?",
]

records = load_documents(DATA_DIR)
chunks = create_chunks(records)
retriever = BM25Retriever(chunks)

print(f"Registros: {len(records)}")
print(f"Fragmentos: {len(chunks)}")

for question in questions:
    print("\n" + "=" * 80)
    print(f"Pregunta: {question}")
    for position, result in enumerate(retriever.search(question, top_k=3), start=1):
        print(
            f"{position}. {result.chunk.source} - {result.chunk.location} "
            f"(score={result.score:.3f})"
        )
        print(result.chunk.content[:240].replace("\n", " ") + "...")
