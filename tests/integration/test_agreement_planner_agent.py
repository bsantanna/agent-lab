import os
from pathlib import Path
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestAgreementPlannerAgent:
    def _create_agent(self, client):
        # create integration
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://api.x.ai/v1/",
                "api_key": os.environ["XAI_API_KEY"],
                "integration_type": "xai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        # create llm
        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "grok-2-vision",
            },
        )
        language_model_id = response_2.json()["id"]

        # create agent
        return client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "agreement_planner",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(
        self, client, message_content, agent_id=None, attachment_id=None
    ):
        if agent_id is None:
            create_agent_response = self._create_agent(client)
            agent_id = create_agent_response.json()["id"]

        return client.post(
            "/messages/post",
            json={
                "message_role": "human",
                "message_content": message_content,
                "agent_id": agent_id,
                "attachment_id": attachment_id,
            },
        )

    def _upload_file(self, client, filename: str, content_type: str):
        current_dir = Path(__file__).parent
        file_path = f"{current_dir}/{filename}"

        # when
        with open(file_path, "rb") as file:
            upload_response = client.post(
                url="/attachments/upload",
                files={"file": (filename, file, content_type)},
            )

        return upload_response

    @pytest.mark.asyncio
    async def test_financial_struggle_flow(self, client):
        # given
        message_content = "Hello, my name is Bruno and I have mortgage debts, I pay an annual rate of 1.89%, totaling 225,000.00 with a monthly installment of 810. It's a 25-year financing, with 5 years already paid. What is the best strategy?"

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

    @pytest.mark.asyncio
    async def test_customer_loss_flow(self, client):
        # given
        message_content = "Hi, I'm Bruno. I bought an executive class seat for a trip to Florianópolis, but I was informed that due to overbooking my seat was occupied and I had to sit in economy class next to the restroom undergoing maintenance, with a seat that did not recline. On top of that, they lost my checked baggage, which contained valuable items such as a notebook and cell phones. What can I do?"

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]
