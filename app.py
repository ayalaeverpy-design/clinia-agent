from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.chunking import chunk_summary, create_chunks
from src.document_loader import document_summary, load_documents
from src.retriever import BM25Retriever

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="ClinIA | Recuperación documental",
    page_icon="🩺",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_knowledge_base() -> tuple[list, list, dict, dict]:
    records = load_documents(DATA_DIR)
    chunks = create_chunks(records)
    return records, chunks, document_summary(records), chunk_summary(chunks)


@st.cache_resource(show_spinner=False)
def build_retriever(chunks: tuple) -> BM25Retriever:
    return BM25Retriever(list(chunks))


st.title("🩺 ClinIA")
st.subheader("Asistente inteligente para Clínica Vida Plena")
st.caption("Proyecto académico con información completamente ficticia")

st.info(
    "Etapa actual: fragmentación y recuperación de información. "
    "Todavía no se genera una respuesta con IA; se muestran los fragmentos que alimentarían al modelo."
)

try:
    records, chunks, document_stats, chunk_stats = load_knowledge_base()
    retriever = build_retriever(tuple(chunks))
except Exception as exc:
    st.error(f"No se pudo preparar la base documental: {exc}")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Documentos", len(document_stats["sources"]))
col2.metric("Registros", document_stats["total_records"])
col3.metric("Fragmentos", chunk_stats["total_chunks"])
col4.metric("Promedio por fragmento", f"{chunk_stats['average_chunk_length']:.0f} caracteres")

st.success("La base documental fue cargada, fragmentada e indexada correctamente.")

st.markdown("## Buscar en la documentación")
query = st.text_input(
    "Escribí una pregunta administrativa",
    placeholder="Ejemplo: ¿Con cuánta anticipación puedo cancelar un turno?",
)

examples = [
    "¿Con cuánta anticipación puedo cancelar un turno?",
    "¿Qué documentos tengo que llevar a la consulta?",
    "¿Cómo protege la clínica mis datos personales?",
    "¿Qué cobertura tiene el plan Integral de SaludPlus?",
]
selected_example = st.selectbox("O elegí una pregunta de prueba", [""] + examples)
active_query = query.strip() or selected_example

if st.button("Buscar información", type="primary", disabled=not active_query):
    results = retriever.search(active_query, top_k=5)
    st.session_state["last_query"] = active_query
    st.session_state["search_results"] = results

if st.session_state.get("search_results") is not None:
    results = st.session_state["search_results"]
    st.markdown(f"### Fragmentos recuperados para: _{st.session_state['last_query']}_")

    if not results:
        st.warning("No se encontraron fragmentos suficientemente relacionados con la consulta.")
    else:
        for position, result in enumerate(results, start=1):
            source_label = f"{result.chunk.source} · {result.chunk.location}"
            with st.expander(
                f"{position}. {source_label} · relevancia {result.score:.3f}",
                expanded=position == 1,
            ):
                st.write(result.chunk.content)
                st.caption(f"ID interno: {result.chunk.chunk_id}")

with st.sidebar:
    st.markdown("### Fuentes cargadas")
    for source, count in document_stats["sources"].items():
        st.write(f"**{source}**")
        st.caption(f"{count} registro(s)")

    st.divider()
    st.markdown("### Estado del proyecto")
    st.write("✅ Lectura de PDF y CSV")
    st.write("✅ Fragmentación con solapamiento")
    st.write("✅ Recuperación local BM25")
    st.write("⏳ Generación con OCI Generative AI")

st.divider()
st.warning(
    "ClinIA brindará información administrativa y general. "
    "No realizará diagnósticos ni recomendará medicamentos."
)
