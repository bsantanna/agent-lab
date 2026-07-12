import os

from tests.simulation.common.config import (
    SIMULATION_LLM_API_BASE,
    SIMULATION_LLM_API_KEY,
    SIMULATION_LLM_MODEL,
)


class LanguageModelBuilder:
    """Builds the integration + language model a simulation agent runs on.

    Defaults to the LAN OpenAI API compatible endpoint configured via the
    SIMULATION_LLM_* environment variables, registered as openai_api_v1.
    Embeddings still go to EMBEDDINGS_ENDPOINT (the test Ollama container
    serving bge-m3, matching the pgvector dump): the env var takes precedence
    over the integration endpoint, and the embeddings setting is pinned to
    bge-m3 after creation. Use with_integration / with_model_tag for agents
    that need a specific provider (e.g. audio transcription).
    """

    def __init__(self, client):
        self._client = client
        self._api_endpoint = SIMULATION_LLM_API_BASE
        self._api_key = SIMULATION_LLM_API_KEY
        self._integration_type = "openai_api_v1"
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
        language_model_id = response_2.json()["id"]

        # pin embeddings to the model served by EMBEDDINGS_ENDPOINT (openai_api_v1
        # integrations default to text-embedding-3-large, which Ollama lacks)
        self._client.post(
            url="/llms/update_setting",
            headers=headers,
            json={
                "language_model_id": language_model_id,
                "setting_key": "embeddings",
                "setting_value": "bge-m3",
            },
        )
        return language_model_id
