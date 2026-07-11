import os

from tests.simulation.common.config import (
    SIMULATION_LLM_API_BASE,
    SIMULATION_LLM_API_KEY,
    SIMULATION_LLM_MODEL,
)


class LanguageModelBuilder:
    """Builds the integration + language model a simulation agent runs on.

    Defaults to the LAN OpenAI API compatible endpoint configured via the
    SIMULATION_LLM_* environment variables, registered as xai_api_v1: the
    chat client is OpenAI compatible, while embeddings keep falling back to
    EMBEDDINGS_ENDPOINT (the test Ollama container serving bge-m3), matching
    the pgvector dump. Use with_integration / with_model_tag for agents that
    need a specific provider (e.g. audio transcription).
    """

    def __init__(self, client):
        self._client = client
        self._api_endpoint = SIMULATION_LLM_API_BASE
        self._api_key = SIMULATION_LLM_API_KEY
        self._integration_type = "xai_api_v1"
        self._language_model_tag = SIMULATION_LLM_MODEL

    def with_integration(self, api_endpoint, api_key, integration_type):
        self._api_endpoint = api_endpoint
        self._api_key = api_key
        self._integration_type = integration_type
        return self

    def with_model_tag(self, language_model_tag):
        self._language_model_tag = language_model_tag
        return self

    def build(self) -> str:
        if not self._api_endpoint or not self._language_model_tag:
            raise RuntimeError(
                "SIMULATION_LLM_API_BASE and SIMULATION_LLM_MODEL must be set "
                "to run simulations against the default LLM endpoint."
            )

        headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}

        # create integration
        response = self._client.post(
            url="/integrations/create",
            headers=headers,
            json={
                "api_endpoint": self._api_endpoint,
                "api_key": self._api_key,
                "integration_type": self._integration_type,
            },
        )
        integration_id = response.json()["id"]

        # create llm
        response_2 = self._client.post(
            url="/llms/create",
            headers=headers,
            json={
                "integration_id": integration_id,
                "language_model_tag": self._language_model_tag,
            },
        )
        return response_2.json()["id"]
