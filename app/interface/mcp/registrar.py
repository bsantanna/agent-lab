from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp import FastMCP

if TYPE_CHECKING:
    from app.core.container import Container


class McpRegistrar:
    """Base class for MCP capability registrars.

    Subclass and override one or more methods to register
    tools, prompts, or resources on the MCP server.
    """

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        """Override in subclasses to register MCP tools."""
        pass  # intentionally empty — subclasses override as needed

    def register_prompts(self, mcp: FastMCP) -> None:
        """Override in subclasses to register MCP prompts."""
        pass  # intentionally empty — subclasses override as needed

    def register_resources(self, mcp: FastMCP) -> None:
        """Override in subclasses to register MCP resources."""
        pass  # intentionally empty — subclasses override as needed
