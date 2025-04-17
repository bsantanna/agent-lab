from abc import ABC

import requests
from langchain_core.tools import tool, BaseTool
from typing_extensions import Annotated

from app.services.agent_types.base import SupervisedWorkflowAgentBase, AgentUtils


class AzureEntraIdOrganizationWorkflowBase(SupervisedWorkflowAgentBase, ABC):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)
        self.token = "TODO"
        # CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        # CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        # TENANT_ID = os.getenv("AZURE_TENANT_ID")
        # AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
        # SCOPES = ["https://graph.microsoft.com/.default"]
        # app = ConfidentialClientApplication(
        #     CLIENT_ID,
        #     authority=AUTHORITY,
        #     client_credential=CLIENT_SECRET,
        # )
        # result = app.acquire_token_for_client(scopes=SCOPES)
        # if "access_token" in result:
        #     self.token = result["access_token"]
        # else:
        #     raise Exception("Could not obtain access token")

    def get_person_search_tool(self) -> BaseTool:
        @tool("person_search")
        def person_search_tool_call(
            name: Annotated[str, "The name of the person for search."],
        ):
            """Use this tool for person search by name."""
            headers = {"Authorization": f"Bearer {self.token}"}
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
            """Get person details by email."""
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"https://graph.microsoft.com/v1.0/users/{email}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user = response.json()
                return f"{user['displayName']} ({user['userPrincipalName']})"
            elif response.status_code == 404:
                return "User not found"
            else:
                return f"Error: {response.status_code} - {response.text}"

        return person_details_tool_call
