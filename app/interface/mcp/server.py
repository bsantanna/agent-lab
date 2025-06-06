import os
import json
import logging
from typing import List, Dict, Any

from fastapi import HTTPException
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

from app.interface.api.messages.schema import MessageRequest
from app.services.agents import AgentService
from app.services.messages import MessageService

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server implementation for Agent Lab"""

    def __init__(self, agent_service: AgentService, message_service: MessageService):
        self.server = Server(
            name=os.getenv("SERVICE_NAME", "Agent-Lab"),
            version=os.getenv("SERVICE_VERSION", "snapshot"),
        )
        self.service_name = os.getenv("SERVICE_NAME", "Agent-Lab").lower()
        self.agent_service = agent_service
        self.message_service = message_service
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers by registering class methods"""
        self.server.list_resources()(self.handle_list_resources)
        self.server.read_resource()(self.handle_read_resource)
        self.server.list_tools()(self.handle_list_tools)
        self.server.call_tool()(self.handle_call_tool)

    async def handle_list_resources(self) -> List[Resource]:
        """List available agent conversation histories as resources"""
        try:
            agents = self.agent_service.get_agents()

            resources = []
            for agent in agents:
                resources.append(
                    Resource(
                        uri=f"{self.service_name}://conversations/{agent.id}",
                        name=f"Agent {agent.agent_name} Conversation History",
                        description=f"Complete conversation history for agent '{agent.agent_name}' ({agent.agent_type})",
                        mimeType="application/json",
                    )
                )
            return resources
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_read_resource(self, uri: str) -> str:
        """Read agent conversation history using /messages/list"""
        try:
            if not uri.startswith(f"{self.service_name}://conversations/"):
                raise HTTPException(status_code=400, detail="Invalid resource URI")

            agent_id = uri.replace(f"{self.service_name}://conversations/", "")
            messages = self.message_service.get_messages(agent_id=agent_id)

            conversation = {
                "agent_id": agent_id,
                "total_messages": len(messages),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.message_role,
                        "content": msg.message_content,
                        "created_at": msg.created_at.isoformat()
                        if msg.created_at
                        else None,
                        "replies_to": msg.replies_to,
                        "response_data": msg.response_data,
                    }
                    for msg in messages
                ],
            }
            return json.dumps(conversation, indent=2)
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_list_tools(self) -> List[Tool]:
        """List available MCP tools"""
        return [
            Tool(
                name="get_agent_conversation",
                description="Retrieve the complete conversation history of a specific agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "The ID of the agent",
                        }
                    },
                    "required": ["agent_id"],
                },
            ),
            Tool(
                name="send_message_to_agent",
                description="Send a message to a specific agent and get the response",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "The ID of the agent",
                        },
                        "message_content": {
                            "type": "string",
                            "description": "Message content",
                        },
                        "message_role": {
                            "type": "string",
                            "description": "Sender role",
                            "default": "user",
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "Optional attachment ID",
                        },
                    },
                    "required": ["agent_id", "message_content"],
                },
            ),
        ]

    async def handle_call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle tool calls"""
        try:
            if name == "get_agent_conversation":
                return await self._get_agent_conversation(arguments)
            elif name == "send_message_to_agent":
                return await self._send_message_to_agent(arguments)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_agent_conversation(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Get agent conversation history using /messages/list"""
        agent_id = arguments.get("agent_id")
        if not agent_id:
            raise ValueError("agent_id is required")

        agent = self.agent_service.get_agent_by_id(agent_id)
        messages = self.message_service.get_messages(agent_id)

        response = {
            "agent": {
                "id": agent.id,
                "name": agent.agent_name,
                "type": agent.agent_type,
                "summary": agent.agent_summary,
                "created_at": agent.created_at.isoformat(),
            },
            "conversation": {
                "total_messages": len(messages),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.message_role,
                        "content": msg.message_content,
                        "created_at": msg.created_at.isoformat()
                        if msg.created_at
                        else None,
                        "replies_to": msg.replies_to,
                        "response_data": msg.response_data,
                    }
                    for msg in messages
                ],
            },
        }
        return [
            TextContent(
                type="text",
                text=f"Conversation history for agent '{agent.agent_name}':\n\n{json.dumps(response, indent=2)}",
            )
        ]

    async def _send_message_to_agent(
        self, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Send message to agent and get response using /messages/post"""
        agent_id = arguments.get("agent_id")
        message_content = arguments.get("message_content")
        message_role = arguments.get("message_role", "user")
        attachment_id = arguments.get("attachment_id")

        if not agent_id or not message_content:
            raise ValueError("agent_id and message_content are required")

        agent = self.agent_service.get_agents(agent_id)
        request = MessageRequest(
            message_role=message_role,
            message_content=message_content,
            agent_id=agent_id,
            attachment_id=attachment_id,
        )
        response_message = self.message_service.create_message(request)

        return [
            TextContent(
                type="text",
                text=f"Message sent to agent '{agent.agent_name}' and response received:\n\n"
                f"Your message: {message_content}\n\n"
                f"Agent response: {response_message.message_content}\n\n"
                f"Response metadata: {json.dumps(response_message.response_data, indent=2) if response_message.response_data else 'None'}",
            )
        ]

    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server
