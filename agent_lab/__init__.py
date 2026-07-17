"""Agent-Lab: a framework for building AI agent applications with FastAPI.

Public surface for downstream apps:

- ``create_app`` / ``RouterMount`` — assemble the FastAPI application.
- ``Container`` — subclass to add providers (services, custom dependencies).
- ``ConfigSource`` — supply configuration from YAML, Vault, or a custom source.

Registration decorators — all discovered through the same package scan
(``create_app(scan_packages=[...])`` or ``agent_lab.agents`` entry points),
all taking the registration key as their first argument, and all resolving
``extra_deps`` names as container providers passed as constructor kwargs.
Omitting ``scan_packages`` scans ``DEFAULT_SCAN_PACKAGES`` (Agent-Lab's
built-in agents and MCP capabilities); an explicit list *replaces* the
defaults, so pass ``[*DEFAULT_SCAN_PACKAGES, "myapp.agents"]`` to extend them
or leave packages out to drop their capabilities:

- ``@discoverable_agent("agent_type", extra_deps=(...))`` — AgentBase subclasses.
- ``@discoverable_mcp_tool("name", ...)`` — an async function as an MCP tool;
  its leading ``container`` parameter is injected and hidden from clients.
- ``@discoverable_mcp_prompt("name", ...)`` — a sync function as an MCP prompt,
  exposed on the full prompt triple (read_prompt_mcp tool / prompts/get /
  prompt:// resource); optional per-tenant overrides via ``agent_type`` +
  ``setting_key``.
- ``@discoverable_mcp_registrar(extra_deps=(...))`` — a full McpRegistrar (or
  ``PromptSetRegistrar``) subclass for advanced tool/prompt/resource sets.
"""

from agent_lab.app_factory import (
    DEFAULT_SCAN_PACKAGES,
    RouterMount,
    bind_agent_registry,
    create_app,
)
from agent_lab.core.config import (
    ConfigSource,
    VaultConfigSource,
    YamlConfigSource,
    default_config_source,
)
from agent_lab.core.container import Container
from agent_lab.infrastructure.metrics.tracing_backends import TracingBackend
from agent_lab.interface.mcp.prompt_registration import discoverable_mcp_prompt
from agent_lab.interface.mcp.prompt_set_registrar import PromptSetRegistrar
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.registrar_registration import discoverable_mcp_registrar
from agent_lab.interface.mcp.tool_registration import discoverable_mcp_tool
from agent_lab.services.agent_types.base import (
    AgentBase,
    AgentUtils,
    ContactSupportAgentBase,
    SupervisedWorkflowAgentBase,
    WebAgentBase,
    WorkflowAgentBase,
)
from agent_lab.services.agent_types.registration import discoverable_agent
from agent_lab.services.agent_types.registry import AgentRegistry

__all__ = [
    "AgentBase",
    "AgentRegistry",
    "AgentUtils",
    "ConfigSource",
    "ContactSupportAgentBase",
    "Container",
    "DEFAULT_SCAN_PACKAGES",
    "McpRegistrar",
    "PromptSetRegistrar",
    "discoverable_agent",
    "discoverable_mcp_prompt",
    "discoverable_mcp_registrar",
    "discoverable_mcp_tool",
    "RouterMount",
    "SupervisedWorkflowAgentBase",
    "TracingBackend",
    "VaultConfigSource",
    "WebAgentBase",
    "WorkflowAgentBase",
    "YamlConfigSource",
    "bind_agent_registry",
    "create_app",
    "default_config_source",
]
