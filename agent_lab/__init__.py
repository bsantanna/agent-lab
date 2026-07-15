"""Agent-Lab: a framework for building AI agent applications with FastAPI.

Public surface for downstream apps:

- ``create_app`` / ``RouterMount`` — assemble the FastAPI application.
- ``Container`` — subclass to add providers (services, MCP registrars, ...).
- ``RegisterAgent`` — decorate AgentBase subclasses; discovered via
  ``create_app(scan_packages=[...])`` or ``agent_lab.agents`` entry points.
- ``ConfigSource`` — supply configuration from YAML, Vault, or a custom source.
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
from agent_lab.interface.mcp.registrar import McpRegistrar
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
    "RegisterAgent",
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
