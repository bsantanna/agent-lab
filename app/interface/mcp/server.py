from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from app.interface.mcp.registrar import McpRegistrar

if TYPE_CHECKING:
    from app.core.container import Container


_SERVER_INSTRUCTIONS = """Agent-Lab is a cloud-native LLM Agent Development and Testing Toolkit.

Available tools:
- get_agent_list: Discover AI agents available on the platform.
- get_message_list: Retrieve conversation history for a specific agent.
- post_message: Send a message to an agent and get the assistant's response.

Available prompts and resources expose default system prompts for each agent type.
Use these to understand agent capabilities or to configure new agent workflows.
"""


def build_mcp_server(
    container: Container,
    registrars: list[McpRegistrar],
) -> FastMCP:
    config = container.config()
    auth = _build_auth(config)

    mcp = FastMCP(
        name=os.getenv("SERVICE_NAME", "Agent-Lab"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        instructions=_SERVER_INSTRUCTIONS,
        auth=auth,
    )

    for registrar in registrars:
        registrar.register_tools(mcp, container)
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

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
