from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import OCISettings


class OCIConfigurationError(RuntimeError):
    """La configuración local de OCI es inválida o incompleta."""


class OCIInferenceError(RuntimeError):
    """OCI no pudo producir una respuesta válida."""


@dataclass(frozen=True, slots=True)
class OCIChatResult:
    text: str
    model_id: str
    finish_reason: str | None = None


class OCIChatClient:
    """Adaptador para OCI Generative AI con autenticación local o de instancia."""

    def __init__(self, settings: OCISettings, *, sdk_module: Any | None = None) -> None:
        self.settings = settings
        self._oci = sdk_module or self._import_oci()

        config, signer = self._build_authentication()
        self._config = config
        self._signer = signer

        if settings.auth_mode == "INSTANCE_PRINCIPAL":
            signer_tenancy = getattr(signer, "tenancy_id", None)
            self.compartment_id = settings.compartment_id or signer_tenancy
        else:
            self.compartment_id = settings.compartment_id or config.get("tenancy")

        if not self.compartment_id:
            raise OCIConfigurationError(
                "No se pudo determinar el compartimiento. Definí OCI_COMPARTMENT_ID."
            )

        client_kwargs: dict[str, Any] = {
            "retry_strategy": self._oci.retry.DEFAULT_RETRY_STRATEGY,
        }
        if signer is not None:
            client_kwargs["signer"] = signer
        if settings.endpoint:
            client_kwargs["service_endpoint"] = settings.endpoint

        try:
            self._client = (
                self._oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config,
                    **client_kwargs,
                )
            )
        except Exception as exc:  # pragma: no cover - depende del SDK real
            raise OCIConfigurationError(
                f"No se pudo inicializar el cliente OCI: {exc}"
            ) from exc

    @staticmethod
    def _import_oci() -> Any:
        try:
            import oci
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise OCIConfigurationError(
                "Falta instalar el paquete 'oci'. Ejecutá: pip install -r requirements.txt"
            ) from exc
        return oci

    def _build_authentication(self) -> tuple[dict[str, Any], Any | None]:
        if self.settings.auth_mode == "INSTANCE_PRINCIPAL":
            try:
                signer = (
                    self._oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                )
            except Exception as exc:
                raise OCIConfigurationError(
                    "No se pudo obtener la identidad de la instancia OCI. "
                    "Verificá el grupo dinámico y la política IAM."
                ) from exc

            region = self.settings.region or getattr(signer, "region", None)
            if not region:
                raise OCIConfigurationError(
                    "No se pudo determinar la región para Instance Principal."
                )
            return {"region": region}, signer

        if not self.settings.config_file.exists():
            raise OCIConfigurationError(
                f"No existe el archivo OCI: {self.settings.config_file}"
            )

        try:
            config = self._oci.config.from_file(
                file_location=str(self.settings.config_file),
                profile_name=self.settings.config_profile,
            )
            self._oci.config.validate_config(config)
        except Exception as exc:
            raise OCIConfigurationError(
                f"Configuración OCI inválida: {exc}"
            ) from exc

        if self.settings.region:
            config["region"] = self.settings.region
        return config, None

    @staticmethod
    def _combine_prompts(system_prompt: str, user_prompt: str) -> str:
        """Integra instrucciones y pregunta en un único mensaje compatible con Gemini."""

        return (
            "INSTRUCCIONES OBLIGATORIAS:\n"
            f"{system_prompt.strip()}\n\n"
            "SOLICITUD DEL USUARIO:\n"
            f"{user_prompt.strip()}"
        )

    def chat(self, *, system_prompt: str, user_prompt: str) -> OCIChatResult:
        models = self._oci.generative_ai_inference.models
        combined_prompt = self._combine_prompts(system_prompt, user_prompt)

        chat_request = models.GenericChatRequest(
            api_format="GENERIC",
            messages=[
                models.UserMessage(
                    content=[
                        models.TextContent(
                            type="TEXT",
                            text=combined_prompt,
                        )
                    ],
                )
            ],
            is_stream=False,
            num_generations=1,
            temperature=self.settings.temperature,
            top_p=self.settings.top_p,
            max_tokens=self.settings.max_tokens,
        )

        details = models.ChatDetails(
            compartment_id=self.compartment_id,
            serving_mode=models.OnDemandServingMode(
                serving_type="ON_DEMAND",
                model_id=self.settings.model_id,
            ),
            chat_request=chat_request,
        )

        try:
            response = self._client.chat(chat_details=details)
            text, finish_reason = self._extract_text(response.data)
        except Exception as exc:  # pragma: no cover - llamada externa
            raise OCIInferenceError(
                f"Error al consultar OCI Generative AI: {exc}"
            ) from exc

        return OCIChatResult(
            text=text,
            model_id=self.settings.model_id,
            finish_reason=finish_reason,
        )

    @staticmethod
    def _extract_text(data: Any) -> tuple[str, str | None]:
        chat_response = getattr(data, "chat_response", None)
        if chat_response is None:
            chat_response = getattr(data, "chatResponse", None)
        if chat_response is None:
            chat_response = data

        choices = getattr(chat_response, "choices", None) or []
        if not choices:
            raise OCIInferenceError(
                "OCI devolvió una respuesta sin opciones de texto"
            )

        choice = choices[0]
        message = getattr(choice, "message", None)
        content_items = getattr(message, "content", None) or []
        texts = [
            str(getattr(item, "text", "")).strip()
            for item in content_items
            if getattr(item, "text", None)
        ]
        text = "\n".join(part for part in texts if part).strip()

        if not text:
            refusal = getattr(message, "refusal", None)
            if refusal:
                text = str(refusal).strip()
        if not text:
            raise OCIInferenceError(
                "OCI devolvió una respuesta sin contenido de texto"
            )

        return text, getattr(choice, "finish_reason", None)
