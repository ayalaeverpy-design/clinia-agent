from dataclasses import dataclass

from src.agent import ClinIAAgent
from src.models import DocumentChunk, SearchResult
from src.oci_client import OCIChatResult
from src.prompts import NO_CONTEXT_MESSAGE


class FakeRetriever:
    def __init__(self, results):
        self.results = results

    def search(self, query, top_k=5):
        return self.results[:top_k]


@dataclass
class FakeOCIClient:
    text: str = "Respuesta basada en documentos."
    calls: int = 0

    def chat(self, *, system_prompt, user_prompt):
        self.calls += 1
        return OCIChatResult(text=self.text, model_id="fake-model")


def _result():
    return SearchResult(
        chunk=DocumentChunk(
            content="Se puede cancelar con 24 horas.",
            source="cancelaciones.pdf",
            document_type="pdf",
            chunk_id="x",
            page=1,
        ),
        score=3.0,
    )


def test_agent_uses_oci_when_context_exists() -> None:
    client = FakeOCIClient()
    agent = ClinIAAgent(FakeRetriever([_result()]), client)
    response = agent.answer("¿Cuándo puedo cancelar?")
    assert response.used_oci is True
    assert response.model_id == "fake-model"
    assert client.calls == 1
    assert response.sources


def test_agent_skips_oci_for_medical_advice() -> None:
    client = FakeOCIClient()
    agent = ClinIAAgent(FakeRetriever([_result()]), client)
    response = agent.answer("¿Qué medicamento puedo tomar?")
    assert response.used_oci is False
    assert client.calls == 0


def test_agent_returns_fallback_without_context() -> None:
    client = FakeOCIClient()
    agent = ClinIAAgent(FakeRetriever([]), client)
    response = agent.answer("¿Tienen estacionamiento?")
    assert response.response_type == "no_context"
    assert response.used_oci is False
    assert response.sources == ()


def test_agent_hides_sources_when_model_returns_no_context() -> None:
    client = FakeOCIClient(text=NO_CONTEXT_MESSAGE)
    agent = ClinIAAgent(FakeRetriever([_result()]), client)
    response = agent.answer("¿Tienen estacionamiento gratuito?")
    assert response.response_type == "no_context"
    assert response.used_oci is True
    assert response.sources == ()
    assert response.answer == NO_CONTEXT_MESSAGE
