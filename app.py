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
    page_title="ClinIA | Asistente administrativo",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1500px;}
        .clinia-hero {
            padding: 1.3rem 1.5rem;
            border: 1px solid rgba(120, 130, 255, 0.25);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(91, 72, 255, 0.14), rgba(14, 165, 233, 0.08));
            margin-bottom: 1rem;
        }
        .clinia-hero h1 {margin: 0; font-size: 2.15rem;}
        .clinia-hero p {margin: .45rem 0 0; opacity: .82;}
        .clinia-badge {
            display: inline-block;
            padding: .25rem .65rem;
            border-radius: 999px;
            border: 1px solid rgba(120, 130, 255, .35);
            margin-right: .35rem;
            font-size: .82rem;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, .18);
            border-radius: 14px;
            padding: .8rem 1rem;
        }
        [data-testid="stChatMessage"] {border-radius: 16px;}
    </style>
    """,
    unsafe_allow_html=True,
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


st.markdown(
    """
    <div class="clinia-hero">
      <h1>🩺 ClinIA</h1>
      <p>Asistente inteligente para consultas administrativas de Clínica Vida Plena.</p>
      <div style="margin-top:.8rem">
        <span class="clinia-badge">RAG documental</span>
        <span class="clinia-badge">OCI Generative AI</span>
        <span class="clinia-badge">PDF + CSV</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
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
    st.success("Base documental indexada y conexión con OCI disponibles.")
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
    st.markdown("## ClinIA")
    st.caption("Consultas administrativas basadas en documentos")
    st.divider()
    st.markdown("### Preguntas de prueba")
    for index, example in enumerate(examples):
        if st.button(example, key=f"example_{index}", use_container_width=True):
            st.session_state["pending_question"] = example

    st.divider()
    st.markdown("### Estado del agente")
    st.write("✅ Lectura de PDF y CSV")
    st.write("✅ Fragmentación documental")
    st.write("✅ Recuperación BM25 enfocada")
    st.write("✅ Generación con OCI" if oci_ready else "⚠️ Generación con OCI")
    st.write("✅ Fuentes trazables")
    st.write("✅ Restricciones médicas")

    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("model_id"):
            st.caption(f"Respuesta generada con {message['model_id']} · contexto documental recuperado")
        if message.get("sources"):
            with st.expander("📚 Fuentes utilizadas"):
                for source in message["sources"]:
                    st.markdown(f"**{source['label']}**")
                    st.caption(f"Puntaje de relevancia: {source['score']:.3f}")
                    st.write(source["content"])

pending = st.session_state.pop("pending_question", None)
question = st.chat_input(
    "Consultá sobre turnos, cancelaciones, privacidad, convenios o indicaciones",
    disabled=not oci_ready,
)
active_question = question or pending

if active_question and agent is not None:
    st.session_state.messages.append({"role": "user", "content": active_question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_question)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            with st.spinner("Buscando evidencia y redactando la respuesta..."):
                response = agent.answer(active_question)
            st.markdown(response.answer)

            source_payload = []
            if response.sources:
                with st.expander("📚 Fuentes utilizadas", expanded=False):
                    for result in response.sources:
                        label = f"{result.chunk.source} · {result.chunk.location}"
                        st.markdown(f"**{label}**")
                        st.caption(f"Puntaje de relevancia: {result.score:.3f}")
                        st.write(result.chunk.content)
                        source_payload.append(
                            {
                                "label": label,
                                "score": result.score,
                                "content": result.chunk.content,
                            }
                        )

            if response.model_id and response.used_oci:
                st.caption(
                    f"Respuesta generada con {response.model_id} · tipo: {response.response_type}"
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": source_payload,
                    "model_id": response.model_id if response.used_oci else None,
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
