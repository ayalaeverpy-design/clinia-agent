from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.document_loader import document_summary, load_documents

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="ClinIA | Asistente de Clínica",
    page_icon="🩺",
    layout="wide",
)

st.title("🩺 ClinIA")
st.subheader("Asistente inteligente para Clínica Vida Plena")
st.caption("Proyecto académico con información completamente ficticia")

st.info(
    "Etapa actual: validación de la carga documental. "
    "La integración con el modelo de inteligencia artificial se realizará en los próximos pasos."
)

try:
    records = load_documents(DATA_DIR)
    summary = document_summary(records)
except Exception as exc:
    st.error(f"No se pudieron cargar los documentos: {exc}")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Documentos", len(summary["sources"]))
col2.metric("Registros extraídos", summary["total_records"])
col3.metric("Caracteres procesados", f"{summary['total_characters']:,}".replace(",", "."))

st.success("Los documentos PDF y CSV fueron procesados correctamente.")

st.markdown("### Fuentes disponibles")
for source, count in summary["sources"].items():
    st.write(f"- **{source}**: {count} registro(s)")

st.markdown("### Inspeccionar contenido extraído")
sources = list(summary["sources"].keys())
selected_source = st.selectbox("Seleccioná un documento", sources)
selected_records = [record for record in records if record.source == selected_source]

for index, record in enumerate(selected_records[:8], start=1):
    location = f"Página {record.page}" if record.page else f"Fila {record.row}"
    with st.expander(f"{index}. {location}"):
        st.text(record.content)

if len(selected_records) > 8:
    st.caption(f"Se muestran los primeros 8 de {len(selected_records)} registros.")

st.divider()
st.warning(
    "ClinIA brindará información administrativa y general. "
    "No realizará diagnósticos ni recomendará medicamentos."
)
