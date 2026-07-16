"""Agent-Lab: a framework for building AI agent applications with FastAPI.

Public surface for downstream apps:

- ``create_app`` / ``RouterMount`` — assemble the FastAPI application.
- ``Container`` — subclass to add providers (services, custom dependencies).
- ``ConfigSource`` — supply configuration from YAML, Vault, or a custom source.

Registration decorators — all discovered through the same pass
(``create_app(scan_packages=[...])`` or ``agent_lab.agents`` entry points),
all taking the registration key as their first argument, and all resolving
``extra_deps`` names as container providers passed as constructor kwargs:

- ``@RegisterAgent("agent_type", extra_deps=(...))`` — AgentBase subclasses.
- ``@RegisterMcpTool("name", ...)`` — an async function as an MCP tool;
  its leading ``container`` parameter is injected and hidden from clients.
- ``@RegisterMcpPrompt("name", ...)`` — a sync function as an MCP prompt,
  exposed on the full prompt triple (read_prompt_mcp tool / prompts/get /
  prompt:// resource); optional per-tenant overrides via ``agent_type`` +
  ``setting_key``.
- ``@RegisterMcpRegistrar(extra_deps=(...))`` — a full McpRegistrar (or
  ``PromptSetRegistrar``) subclass for advanced tool/prompt/resource sets.
"""

from agent_lab.app_factory import RouterMount, bind_agent_registry, create_app
from agent_lab.core.config import (
    ConfigSource,
    VaultConfigSource,
    YamlConfigSource,
    default_config_source,
)
from agent_lab.core.container import Container
from agent_lab.infrastructure.metrics.tracing_backends import TracingBackend
from agent_lab.interface.mcp.prompt_registration import RegisterMcpPrompt
from agent_lab.interface.mcp.prompt_set_registrar import PromptSetRegistrar
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.registrar_registration import RegisterMcpRegistrar
from agent_lab.interface.mcp.tool_registration import RegisterMcpTool
from agent_lab.services.agent_types.base import (
    AgentBase,
    AgentUtils,
    ContactSupportAgentBase,
    SupervisedWorkflowAgentBase,
    WebAgentBase,
    WorkflowAgentBase,
)
from agent_lab.services.agent_types.registration import RegisterAgent
from agent_lab.services.agent_types.registry import AgentRegistry

__all__ = [
    "AgentBase",
    "AgentRegistry",
    "AgentUtils",
    "ConfigSource",
    "ContactSupportAgentBase",
    "Container",
    "McpRegistrar",
    "PromptSetRegistrar",
    "RegisterAgent",
    "RegisterMcpPrompt",
    "RegisterMcpRegistrar",
    "RegisterMcpTool",
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
