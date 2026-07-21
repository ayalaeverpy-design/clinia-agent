from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.agent import ClinIAAgent
from src.chunking import chunk_summary, create_chunks
from src.config import load_oci_settings
from src.document_loader import document_summary, load_documents
from src.oci_client import OCIChatClient, OCIConfigurationError, OCIInferenceError
from src.retriever import BM25Retriever

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="ClinIA | Asistente médico administrativo",
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


@st.cache_resource(show_spinner=False)
def build_agent(_retriever: BM25Retriever) -> ClinIAAgent:
    settings = load_oci_settings()
    return ClinIAAgent(_retriever, OCIChatClient(settings))


st.title("🩺 ClinIA")
st.subheader("Asistente inteligente para Clínica Vida Plena")
st.caption("Proyecto académico · La clínica, los convenios y las políticas son ficticios")

try:
    records, chunks, document_stats, chunk_stats = load_knowledge_base()
    retriever = build_retriever(tuple(chunks))
except Exception as exc:
    st.error(f"No se pudo preparar la base documental: {exc}")
    st.stop()

try:
    agent = build_agent(retriever)
    oci_ready = True
    oci_error = None
except OCIConfigurationError as exc:
    agent = None
    oci_ready = False
    oci_error = str(exc)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Documentos", len(document_stats["sources"]))
col2.metric("Registros", document_stats["total_records"])
col3.metric("Fragmentos", chunk_stats["total_chunks"])
col4.metric("Modelo", "Gemini 2.5 Flash" if oci_ready else "OCI pendiente")

if oci_ready:
    st.success("Base documental y conexión local con OCI preparadas correctamente.")
else:
    st.error(f"La configuración de OCI todavía no está lista: {oci_error}")

examples = [
    "¿Con cuánta anticipación puedo cancelar un turno?",
    "¿Qué documentos tengo que llevar a la consulta?",
    "¿Cómo protege la clínica mis datos personales?",
    "¿Qué cobertura tiene el plan Integral de SaludPlus?",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### Preguntas de prueba")
    for index, example in enumerate(examples):
        if st.button(example, key=f"example_{index}", use_container_width=True):
            st.session_state["pending_question"] = example

    st.divider()
    st.markdown("### Estado")
    st.write("✅ Lectura de PDF y CSV")
    st.write("✅ Fragmentación documental")
    st.write("✅ Recuperación BM25")
    st.write("✅ Generación con OCI" if oci_ready else "⚠️ Generación con OCI")
    st.write("✅ Fuentes trazables")

    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Fuentes utilizadas"):
                for source in message["sources"]:
                    st.markdown(f"**{source['label']}**")
                    st.caption(f"Relevancia: {source['score']:.3f}")
                    st.write(source["content"])

pending = st.session_state.pop("pending_question", None)
question = st.chat_input(
    "Consultá sobre turnos, cancelaciones, privacidad, convenios o indicaciones",
    disabled=not oci_ready,
)
active_question = question or pending

if active_question and agent is not None:
    st.session_state.messages.append({"role": "user", "content": active_question})
    with st.chat_message("user"):
        st.markdown(active_question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando los documentos de la clínica..."):
                response = agent.answer(active_question)
            st.markdown(response.answer)

            source_payload = []
            if response.sources:
                with st.expander("Fuentes utilizadas", expanded=True):
                    for result in response.sources:
                        label = f"{result.chunk.source} · {result.chunk.location}"
                        st.markdown(f"**{label}**")
                        st.caption(f"Relevancia: {result.score:.3f}")
                        st.write(result.chunk.content)
                        source_payload.append(
                            {
                                "label": label,
                                "score": result.score,
                                "content": result.chunk.content,
                            }
                        )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": source_payload,
                }
            )
        except OCIInferenceError as exc:
            error_message = (
                "No pude generar la respuesta en OCI. Revisá la conexión, los permisos y "
                f"el estado de la cuenta. Detalle: {exc}"
            )
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message, "sources": []}
            )

st.divider()
st.warning(
    "ClinIA brinda información administrativa. No realiza diagnósticos, no interpreta "
    "síntomas y no recomienda medicamentos."
)
