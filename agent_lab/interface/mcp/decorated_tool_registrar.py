from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp import FastMCP

from agent_lab.interface.mcp import tool_registration
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.registrar_registration import RegisterMcpRegistrar

if TYPE_CHECKING:
    from agent_lab.core.container import Container


@RegisterMcpRegistrar()
class DecoratedToolRegistrar(McpRegistrar):
    """Registers every ``@RegisterMcpTool``-decorated function as an MCP tool.

    Container is bound into each function and hidden from the client-facing
    schema, so a tool author writes a plain async function instead of a full
    ``McpRegistrar`` subclass. Takes no ``extra_deps`` — the live container is
    handed to ``register_tools`` and threaded into each tool at call time.
    """

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        for descriptor in tool_registration.registered_tools():
            bound_fn = tool_registration.bind_container(descriptor, container)
            mcp.tool(
                name=descriptor.name,
                description=descriptor.description,
                annotations=descriptor.annotations,
            )(bound_fn)
