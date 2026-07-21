from pathlib import Path
from types import SimpleNamespace

from src.config import OCISettings
from src.oci_client import OCIChatClient


class FakeInferenceClient:
    def __init__(self, config, **kwargs):
        self.config = config
        self.kwargs = kwargs


class FakeSigner:
    tenancy_id = "ocid1.tenancy.oc1..fake"
    region = "us-ashburn-1"


class FakeOCI:
    retry = SimpleNamespace(DEFAULT_RETRY_STRATEGY=object())
    auth = SimpleNamespace(
        signers=SimpleNamespace(
            InstancePrincipalsSecurityTokenSigner=lambda: FakeSigner()
        )
    )
    generative_ai_inference = SimpleNamespace(
        GenerativeAiInferenceClient=FakeInferenceClient
    )


def _settings(auth_mode: str) -> OCISettings:
    return OCISettings(
        auth_mode=auth_mode,
        config_file=Path("/archivo/inexistente"),
        config_profile="DEFAULT",
        compartment_id=None,
        region="us-ashburn-1",
        model_id="google.gemini-2.5-flash",
        endpoint=None,
        max_tokens=1000,
        temperature=0.15,
        top_p=0.9,
    )


def test_instance_principal_does_not_require_config_file() -> None:
    client = OCIChatClient(
        _settings("INSTANCE_PRINCIPAL"),
        sdk_module=FakeOCI,
    )

    assert client.compartment_id == "ocid1.tenancy.oc1..fake"
    assert client._config == {"region": "us-ashburn-1"}
    assert isinstance(client._signer, FakeSigner)
    assert client._client.kwargs["signer"] is client._signer
