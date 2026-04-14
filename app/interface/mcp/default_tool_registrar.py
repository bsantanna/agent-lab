from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.schema import (
    AgentItem,
    MessageItem,
    PostMessageResult,
    _get_mcp_schema,
)

if TYPE_CHECKING:
    from app.core.container import Container


class DefaultToolRegistrar(McpRegistrar):
    """Registers the default Agent-Lab MCP tools."""

    def register_tools(self, mcp: FastMCP, container: Container) -> None:

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
