import json
import os
from abc import ABC

import requests
from langchain_core.tools import tool, BaseTool
from msal import ConfidentialClientApplication
from typing_extensions import Annotated

from app.services.agent_types.base import SupervisedWorkflowAgentBase, AgentUtils


class AzureEntraIdOrganizationWorkflowBase(SupervisedWorkflowAgentBase, ABC):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def get_token(self) -> str:
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" in result:
            return result["access_token"]
        else:
            self.logger.error("Could not obtain Azure access token")
            return ""

    def get_person_search_tool(self) -> BaseTool:
        @tool("person_search")
        def person_search_tool_call(
            name: Annotated[str, "The name of the person for search."],
        ):
            """Use this tool to search for more information about a given person profile information within the organization."""
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            url = f"https://graph.microsoft.com/v1.0/users?$filter=startswith(displayName,'{name}')"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                users = response.json().get("value", [])
                if users:
                    result = [
                        f"{user['displayName']} ({user['userPrincipalName']})"
                        for user in users
                    ]
                    return "\n".join(result)
                else:
                    return "No users found"
            else:
                return f"Error: {response.status_code} - {response.text}"

        return person_search_tool_call

    def get_person_details_tool(self) -> BaseTool:
        @tool("person_details")
        def person_details_tool_call(email: Annotated[str, "The email of the person."]):
            """Use this tool to get details about person profile information."""
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            url = f"https://graph.microsoft.com/v1.0/users/{email}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user = response.json()
                return json.dumps(user)
            elif response.status_code == 404:
                return "User not found"
            else:
                return f"Error: {response.status_code} - {response.text}"

        return person_details_tool_call
