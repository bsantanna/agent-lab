import os

from dependency_injector.wiring import Provide, inject
from fastapi import Body, APIRouter, Depends
from fastapi.responses import JSONResponse
import logging

from app.core.container import Container
from app.interface.mcp.schema import ReadResourceRequest, ToolCallRequest
from app.interface.mcp.server import MCPServer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/resources/read")
@inject
async def read_resource(
    request: ReadResourceRequest = Body(...),
    mcp_server: MCPServer = Depends(Provide[Container.mcp_server]),
):
    try:
        uri = request.params.uri
        content = await mcp_server.handle_read_resource(uri)
        return JSONResponse(
            {
                "contents": [
                    {"uri": uri, "mimeType": "application/json", "text": content}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error reading resource: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/initialize")
async def initialize_mcp():
    try:
        return JSONResponse(
            {
                "protocolVersion": "2024-10-07",
                "capabilities": {
                    "resources": {"subscribe": False, "listChanged": False},
                    "tools": {"listChanged": False},
                    "prompts": {"listChanged": False},
                    "logging": {},
                },
                "serverInfo": {
                    "name": os.getenv("SERVICE_NAME", "Agent-Lab"),
                    "version": os.getenv("SERVICE_VERSION", "snapshot"),
                },
            }
        )
    except Exception as e:
        logger.error(f"MCP initialization error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/resources/list")
@inject
async def list_resources(
    mcp_server: MCPServer = Depends(Provide[Container.mcp_server]),
):
    try:
        resources = await mcp_server.handle_list_resources()
        return JSONResponse(
            {
                "resources": [
                    {
                        "uri": resource.uri.unicode_string(),
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mimeType,
                    }
                    for resource in resources
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/tools/list")
@inject
async def list_tools(mcp_server: MCPServer = Depends(Provide[Container.mcp_server])):
    try:
        tools = await mcp_server.handle_list_tools()
        return JSONResponse(
            {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in tools
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/tools/call")
@inject
async def call_tool(
    request: ToolCallRequest = Body(...),
    mcp_server: MCPServer = Depends(Provide[Container.mcp_server]),
):
    try:
        tool_name = request.params.name
        arguments = request.params.arguments
        result = await mcp_server.handle_call_tool(tool_name, arguments)
        return JSONResponse(
            {
                "content": [
                    {"type": content.type, "text": content.text} for content in result
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/manifest")
async def get_manifest():
    """Get MCP server manifest"""
    return JSONResponse(
        {
            "name": os.getenv("SERVICE_NAME", "Agent-Lab"),
            "version": os.getenv("SERVICE_VERSION", "snapshot"),
            "description": "MCP server for Agent Lab - manage and interact with LangGraph agents",
            "author": f"{os.getenv('SERVICE_NAME', 'Agent-Lab')} Team",
            "license": "MIT",
            "homepage": os.getenv("API_BASE_URL", "https://agent-lab.btech.software"),
            "repository": "https://github.com/bsantanna/agent-lab",
            "capabilities": {
                "resources": True,
                "tools": True,
                "prompts": False,
                "logging": True,
            },
            "transport": {
                "type": "http",
                "baseUrl": f"{os.getenv('API_BASE_URL', 'https://agent-lab.btech.software')}/mcp",
            },
        }
    )
