from dataclasses import dataclass, field

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
    responses: list[str] = field(default_factory=list)
    calls: int = 0

    def chat(self, *, system_prompt, user_prompt):
        self.calls += 1
        if self.responses:
            text = self.responses.pop(0)
        else:
            text = self.text
        return OCIChatResult(text=text, model_id="fake-model")


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


def test_agent_retries_when_first_answer_is_incomplete() -> None:
    client = FakeOCIClient(
        responses=[
            "Puede cancelar hasta 24 horas antes, pero los procedimientos deben cancelarse con",
            "Puede cancelar sin costo hasta 24 horas antes. Los procedimientos especiales deben cancelarse con 48 horas de anticipación.",
        ]
    )
    agent = ClinIAAgent(FakeRetriever([_result()]), client)
    response = agent.answer("¿Cuándo puedo cancelar?")
    assert client.calls == 2
    assert response.answer.endswith(".")
    assert "48 horas" in response.answer


def test_agent_never_exposes_an_incomplete_final_fragment() -> None:
    client = FakeOCIClient(
        responses=[
            "Puede cancelar hasta 24 horas antes y",
            "Puede cancelar hasta 24 horas antes. Los procedimientos deben cancelarse con",
        ]
    )
    agent = ClinIAAgent(FakeRetriever([_result()]), client)
    response = agent.answer("¿Cuándo puedo cancelar?")
    assert client.calls == 2
    assert response.answer == "Puede cancelar hasta 24 horas antes."
    assert response.answer.endswith(".")
