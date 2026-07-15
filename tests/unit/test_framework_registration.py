import sys
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from agent_lab.core.config import (
    ConfigSource,
    YamlConfigSource,
    default_config_source,
)
from agent_lab.domain.exceptions.base import ConfigurationError
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.server import build_mcp_server
from agent_lab.services.agent_types import discovery, registration
from agent_lab.services.agent_types.base import AgentBase
from agent_lab.services.agent_types.registration import RegisterAgent
from agent_lab.services.agent_types.registry import AgentRegistry


@pytest.fixture(autouse=True)
def restore_registry():
    snapshot = dict(registration._registry)
    yield
    registration._registry.clear()
    registration._registry.update(snapshot)


def make_agent_class():
    class DummyAgent(AgentBase):
        def __init__(self, agent_utils, **extra):
            self.agent_utils = agent_utils
            self.extra = extra

        def create_default_settings(self, agent_id, schema):
            pass

        def get_input_params(self, message_request, schema):
            return {}

        def process_message(self, message_request, schema):
            return None

    return DummyAgent


class TestRegisterAgent:
    def test_registers_agent_type(self):
        cls = RegisterAgent("dummy_type")(make_agent_class())
        assert registration.is_registered("dummy_type")
        assert "dummy_type" in registration.registered_types()
        assert registration.get_descriptor("dummy_type").agent_cls is cls

    def test_duplicate_type_different_class_raises(self):
        RegisterAgent("dummy_type")(make_agent_class())
        with pytest.raises(ValueError, match="already registered"):
            RegisterAgent("dummy_type")(make_agent_class())

    def test_same_class_reregistration_is_idempotent(self):
        cls = make_agent_class()
        RegisterAgent("dummy_type")(cls)
        RegisterAgent("dummy_type")(cls)
        assert registration.get_descriptor("dummy_type").agent_cls is cls

    def test_non_agent_base_raises(self):
        with pytest.raises(TypeError, match="AgentBase subclass"):
            RegisterAgent("dummy_type")(object)

    def test_extra_deps_recorded(self):
        RegisterAgent("dummy_type", extra_deps=("markets_service",))(make_agent_class())
        assert registration.get_descriptor("dummy_type").extra_deps == (
            "markets_service",
        )


class FakeContainer:
    """Duck-typed container: providers are attributes returning instances."""

    def __init__(self, **providers):
        self.agent_utils = lambda: "utils"
        for name, value in providers.items():
            setattr(self, name, lambda value=value: value)


class TestAgentRegistry:
    def test_resolves_extra_deps_by_provider_name(self):
        RegisterAgent("dummy_type", extra_deps=("markets_service",))(make_agent_class())
        registry = AgentRegistry(FakeContainer(markets_service="markets"))
        agent = registry.get_agent("dummy_type")
        assert agent.agent_utils == "utils"
        assert agent.extra == {"markets_service": "markets"}

    def test_memoizes_instances(self):
        RegisterAgent("dummy_type")(make_agent_class())
        registry = AgentRegistry(FakeContainer())
        assert registry.get_agent("dummy_type") is registry.get_agent("dummy_type")

    def test_missing_provider_raises_configuration_error(self):
        RegisterAgent("dummy_type", extra_deps=("missing_service",))(make_agent_class())
        registry = AgentRegistry(FakeContainer())
        with pytest.raises(ConfigurationError) as exc_info:
            registry.get_agent("dummy_type")
        assert "missing_service" in exc_info.value.detail
        assert "FakeContainer" in exc_info.value.detail

    def test_get_agent_types_reflects_registrations(self):
        RegisterAgent("dummy_type")(make_agent_class())
        registry = AgentRegistry(FakeContainer())
        assert "dummy_type" in registry.get_agent_types()


class TestDiscovery:
    def test_scan_packages_imports_modules_and_fires_decorators(self, tmp_path):
        package_dir = tmp_path / "dummy_agents_pkg"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        (package_dir / "agent.py").write_text(
            textwrap.dedent("""
                from agent_lab.services.agent_types.base import AgentBase
                from agent_lab.services.agent_types.registration import RegisterAgent

                @RegisterAgent("scanned_dummy")
                class ScannedDummyAgent(AgentBase):
                    def create_default_settings(self, agent_id, schema):
                        pass

                    def get_input_params(self, message_request, schema):
                        return {}

                    def process_message(self, message_request, schema):
                        return None
            """)
        )
        sys.path.insert(0, str(tmp_path))
        try:
            discovery.scan_packages(["dummy_agents_pkg"])
            assert registration.is_registered("scanned_dummy")
        finally:
            sys.path.remove(str(tmp_path))
            sys.modules.pop("dummy_agents_pkg", None)
            sys.modules.pop("dummy_agents_pkg.agent", None)

    def test_load_entry_point_agents_loads_group(self):
        entry_point = MagicMock()
        with patch(
            "agent_lab.services.agent_types.discovery.importlib_metadata.entry_points",
            return_value=[entry_point],
        ) as entry_points:
            discovery.load_entry_point_agents()
        entry_points.assert_called_once_with(group="agent_lab.agents")
        entry_point.load.assert_called_once()


class TestConfigSource:
    def test_yaml_config_source_loads_file(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text(
            "api_base_url: http://localhost\nauth:\n  enabled: false\n"
        )
        config = YamlConfigSource(str(config_file)).load()
        assert config["api_base_url"] == "http://localhost"
        assert config["auth"]["enabled"] is False

    def test_default_config_source_env_branches(self, monkeypatch):
        monkeypatch.setenv("TESTING", "1")
        source = default_config_source()
        assert isinstance(source, YamlConfigSource)
        assert source.path == "config-test.yml"

    def test_custom_config_source_subclass(self):
        class StubConfig(ConfigSource):
            def load(self):
                return {"api_base_url": "http://stub"}

        assert StubConfig().load()["api_base_url"] == "http://stub"


class TestMcpInstructionsComposition:
    def test_fragments_and_extra_instructions_are_appended(self):
        container = MagicMock()
        container.config.return_value = {
            "auth": {"enabled": False},
            "api_base_url": "http://localhost",
        }

        class FragmentRegistrar(McpRegistrar):
            def instructions_fragment(self):
                return "REGISTRAR FRAGMENT"

        mcp = build_mcp_server(
            container,
            [FragmentRegistrar(), McpRegistrar()],
            extra_instructions=("APP FRAGMENT",),
        )
        assert "Agent-Lab" in mcp.instructions
        assert "REGISTRAR FRAGMENT" in mcp.instructions
        assert "APP FRAGMENT" in mcp.instructions
