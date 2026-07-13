from __future__ import annotations

import logging

from app.interface.mcp.schema import _get_mcp_schema
from app.services.agent_settings import AgentSettingService
from app.services.agents import AgentService

logger = logging.getLogger(__name__)


class UserPromptResolver:
    """Looks up the raw prompt template to serve over MCP.

    When an authenticated user has an active agent of the given ``agent_type``
    in their tenant schema and that agent has a non-empty ``setting_key``
    value, the user's template is returned. Otherwise ``default_template``
    is returned. No rendering is performed — the model substitutes any
    placeholders (e.g. ``{{ CURRENT_TIME }}``) on its side.
    """

    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
    ) -> None:
        self._agent_service = agent_service
        self._agent_setting_service = agent_setting_service

    def resolve(
        self,
        agent_type: str,
        setting_key: str,
        default_template: str,
    ) -> str:
        schema = _get_mcp_schema()
        user_template = self._lookup_user_template(schema, agent_type, setting_key)
        return user_template if user_template is not None else default_template

    def _lookup_user_template(
        self, schema: str, agent_type: str, setting_key: str
    ) -> str | None:
        if schema == "public":
            return None
        agent = next(
            (
                a
                for a in self._agent_service.get_agents(schema)
                if a.agent_type == agent_type
            ),
            None,
        )
        if agent is None:
            return None
        for setting in self._agent_setting_service.get_agent_settings(agent.id, schema):
            if setting.setting_key == setting_key:
                value = setting.setting_value
                return value if value and value.strip() else None
        return None
