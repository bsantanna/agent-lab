import os
from pathlib import Path
from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from fastmcp.server.dependencies import get_access_token

from app.core.container import Container
from app.infrastructure.auth.user import get_schema


# -- Response models --


class AgentItem(BaseModel):
    """An AI agent registered on the Agent-Lab platform."""

    id: str = Field(description="Unique agent identifier")
    agent_name: str = Field(description="Human-readable agent name")
    agent_type: str = Field(description="Agent type key (e.g. react_rag, vision_document)")
    agent_summary: str = Field(description="Brief description of the agent's purpose and capabilities")
    language_model_id: str = Field(description="ID of the language model powering this agent")
    is_active: bool = Field(description="Whether the agent is currently active")


class MessageItem(BaseModel):
    """A message in an agent conversation."""

    id: str = Field(description="Unique message identifier")
    message_role: str = Field(description="Role: 'human' or 'assistant'")
    message_content: str = Field(description="Text content of the message")
    agent_id: str = Field(description="ID of the agent this message belongs to")
    response_data: Optional[str] = Field(default=None, description="Structured response data, if any")
    replies_to: Optional[str] = Field(default=None, description="ID of the message this replies to")


class PostMessageResult(BaseModel):
    """Result of sending a message to an agent."""

    id: str = Field(description="ID of the assistant's response message")
    message_content: str = Field(description="The assistant's response text")
    agent_id: str = Field(description="ID of the agent that processed the message")
    response_data: Optional[str] = Field(default=None, description="Structured response data, if any")


# -- Server setup --

_SERVER_INSTRUCTIONS = """Agent-Lab is a cloud-native LLM Agent Development and Testing Toolkit.

Available tools:
- get_agent_list: Discover AI agents available on the platform.
- get_message_list: Retrieve conversation history for a specific agent.
- post_message: Send a message to an agent and get the assistant's response.

Available prompts and resources expose default system prompts for each agent type.
Use these to understand agent capabilities or to configure new agent workflows.
"""


def build_mcp_server(container: Container) -> FastMCP:
    config = container.config()
    auth = _build_auth(config)

    mcp = FastMCP(
        name=os.getenv("SERVICE_NAME", "Agent-Lab"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        instructions=_SERVER_INSTRUCTIONS,
        auth=auth,
    )

    _register_tools(mcp, container)
    _register_prompts(mcp)
    _register_resources(mcp)
    return mcp


def _build_auth(config: dict):
    if not config["auth"]["enabled"]:
        return None

    from fastmcp.server.auth import OAuthProxy
    from fastmcp.server.auth.providers.jwt import JWTVerifier

    auth_url = config["auth"]["url"]
    realm = config["auth"]["realm"]
    realm_base = f"{auth_url}/realms/{realm}"

    return OAuthProxy(
        upstream_authorization_endpoint=f"{realm_base}/protocol/openid-connect/auth",
        upstream_token_endpoint=f"{realm_base}/protocol/openid-connect/token",
        upstream_client_id=config["auth"]["client_id"],
        upstream_client_secret=config["auth"]["client_secret"],
        token_verifier=JWTVerifier(
            jwks_uri=f"{realm_base}/protocol/openid-connect/certs",
            issuer=realm_base,
            audience="account",
            required_scopes=["openid", "profile", "email"],
        ),
        base_url=f"{config['api_base_url']}/mcp",
    )


def _get_mcp_schema() -> str:
    """Derive the tenant DB schema from the MCP access token."""
    access_token = get_access_token()
    if access_token is None:
        return "public"
    sub = access_token.claims.get("sub")
    user_id = f"id_{sub}" if sub else None
    return get_schema(user_id)


def _register_tools(mcp: FastMCP, container: Container) -> None:

    @mcp.tool(
        name="get_agent_list",
        description="List all AI agents registered on the Agent-Lab platform. "
        "Returns each agent's ID, name, type, capabilities summary, "
        "and linked language model. Use this to discover what agents "
        "are available and what they can do.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    async def get_agent_list() -> list[AgentItem]:
        schema = _get_mcp_schema()
        agent_service = container.agent_service()
        agents = agent_service.get_agents(schema)
        return [
            AgentItem(
                id=a.id,
                agent_name=a.agent_name,
                agent_type=a.agent_type,
                agent_summary=a.agent_summary,
                language_model_id=a.language_model_id,
                is_active=a.is_active,
            )
            for a in agents
        ]

    @mcp.tool(
        name="get_message_list",
        description="Retrieve conversation history for a specific agent. "
        "Returns all messages (human and assistant) in chronological order. "
        "Use this to review past interactions or provide context.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    async def get_message_list(
        agent_id: Annotated[
            str,
            Field(description="The unique identifier of the agent whose messages to retrieve"),
        ],
    ) -> list[MessageItem]:
        schema = _get_mcp_schema()
        message_service = container.message_service()
        messages = message_service.get_messages(agent_id, schema)
        return [
            MessageItem(
                id=m.id,
                message_role=m.message_role,
                message_content=m.message_content,
                agent_id=m.agent_id,
                response_data=m.response_data,
                replies_to=m.replies_to,
            )
            for m in messages
        ]

    @mcp.tool(
        name="post_message",
        description="Send a message to an agent and receive the assistant's response. "
        "The message is routed to the appropriate agent processor based on agent type. "
        "Both the human message and the generated response are stored in conversation history.",
        annotations={"readOnlyHint": False, "openWorldHint": False},
    )
    async def post_message(
        agent_id: Annotated[
            str,
            Field(description="The unique identifier of the target agent"),
        ],
        message_content: Annotated[
            str,
            Field(description="The text content of the message to send"),
        ],
        attachment_id: Annotated[
            Optional[str],
            Field(description="Optional ID of a previously uploaded attachment to include"),
        ] = None,
    ) -> PostMessageResult:
        from app.interface.api.messages.schema import MessageRequest

        schema = _get_mcp_schema()
        agent_service = container.agent_service()
        agent_registry = container.agent_registry()
        message_service = container.message_service()

        agent = agent_service.get_agent_by_id(agent_id, schema)
        matching_agent = agent_registry.get_agent(agent.agent_type)

        message_request = MessageRequest(
            agent_id=agent_id,
            message_role="human",
            message_content=message_content,
            attachment_id=attachment_id,
        )

        human_message = message_service.create_message(
            message_role="human",
            message_content=message_content,
            agent_id=agent_id,
            attachment_id=attachment_id,
            schema=schema,
        )

        processed_message = matching_agent.process_message(message_request, schema)

        assistant_message = message_service.create_message(
            message_role="assistant",
            message_content=processed_message.message_content,
            response_data=processed_message.response_data,
            agent_id=processed_message.agent_id,
            replies_to=human_message,
            schema=schema,
        )

        return PostMessageResult(
            id=assistant_message.id,
            message_content=assistant_message.message_content,
            agent_id=assistant_message.agent_id,
            response_data=assistant_message.response_data,
        )


# -- Agent type prompt definitions --

_AGENT_TYPE_PROMPTS = {
    "adaptive_rag": {
        "description": "Adaptive RAG agent — answers queries using retrieved context with grading and rewriting",
        "prompt_file": "adaptive_rag/default_execution_system_prompt.txt",
    },
    "coordinator_planner_supervisor": {
        "description": "Coordinator-Planner-Supervisor multi-agent — handles greetings, plans complex tasks, and delegates to specialized workers",
        "prompt_file": "coordinator_planner_supervisor/default_coordinator_system_prompt.txt",
    },
    "react_rag": {
        "description": "ReAct RAG agent — answers queries with reasoning and tool use over retrieved context",
        "prompt_file": "react_rag/default_execution_system_prompt.txt",
    },
    "test_echo": {
        "description": "Test Echo agent — echoes input back for testing purposes",
        "prompt_file": None,
    },
    "vision_document": {
        "description": "Vision Document agent — analyzes document images and generates structured summaries for RAG",
        "prompt_file": "vision_document/default_execution_system_prompt.txt",
    },
    "voice_memos": {
        "description": "Voice Memos agent — transcribes audio and organizes personal memos",
        "prompt_file": "business/voice_memos/default_coordinator_system_prompt.txt",
    },
}

_PROMPTS_BASE = Path(__file__).parent.parent.parent / "services" / "agent_types"


def _read_prompt(prompt_file: str) -> str:
    return (_PROMPTS_BASE / prompt_file).read_text()


def _make_prompt_fn(file: str):
    def fn() -> str:
        return _read_prompt(file)
    return fn


def _register_prompts(mcp: FastMCP) -> None:
    for agent_type, info in _AGENT_TYPE_PROMPTS.items():
        if info["prompt_file"] is None:
            continue

        fn = _make_prompt_fn(info["prompt_file"])
        fn.__name__ = f"{agent_type}_system_prompt"
        mcp.prompt(
            name=f"{agent_type}_system_prompt",
            description=f"Default system prompt for the {agent_type} agent type. {info['description']}",
        )(fn)


def _register_resources(mcp: FastMCP) -> None:
    for agent_type, info in _AGENT_TYPE_PROMPTS.items():
        if info["prompt_file"] is None:
            continue

        fn = _make_prompt_fn(info["prompt_file"])
        fn.__name__ = f"{agent_type}_system_prompt_resource"
        mcp.resource(
            uri=f"prompt://{agent_type}_system_prompt",
            name=f"{agent_type}_system_prompt",
            description=f"Default system prompt for the {agent_type} agent type. {info['description']}",
        )(fn)
