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
from agent_lab.interface.mcp import (
    bootstrap,
    prompt_registration,
    registrar_registration,
    tool_registration,
)
from agent_lab.interface.mcp.prompt_registration import RegisterMcpPrompt
from agent_lab.interface.mcp.prompt_registry import PromptRegistry
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.registrar_registration import RegisterMcpRegistrar
from agent_lab.interface.mcp.server import build_mcp_server
from agent_lab.interface.mcp.tool_registration import RegisterMcpTool
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


@pytest.fixture(autouse=True)
def restore_mcp_registries():
    registrar_snapshot = dict(registrar_registration._registry)
    tool_snapshot = dict(tool_registration._registry)
    prompt_snapshot = dict(prompt_registration._registry)
    yield
    registrar_registration._registry.clear()
    registrar_registration._registry.update(registrar_snapshot)
    tool_registration._registry.clear()
    tool_registration._registry.update(tool_snapshot)
    prompt_registration._registry.clear()
    prompt_registration._registry.update(prompt_snapshot)


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


class TestRegisterMcpRegistrar:
    def test_registers_registrar_class(self):
        @RegisterMcpRegistrar()
        class DummyRegistrar(McpRegistrar):
            pass

        descriptors = registrar_registration.registered_registrars()
        assert any(d.registrar_cls is DummyRegistrar for d in descriptors)

    def test_records_extra_deps(self):
        @RegisterMcpRegistrar(extra_deps=("prompt_registry",))
        class DepRegistrar(McpRegistrar):
            pass

        descriptor = next(
            d
            for d in registrar_registration.registered_registrars()
            if d.registrar_cls is DepRegistrar
        )
        assert descriptor.extra_deps == ("prompt_registry",)

    def test_non_registrar_raises(self):
        with pytest.raises(TypeError, match="McpRegistrar subclass"):
            RegisterMcpRegistrar()(object)

    def test_same_class_reregistration_is_idempotent(self):
        class Dummy(McpRegistrar):
            pass

        RegisterMcpRegistrar()(Dummy)
        RegisterMcpRegistrar()(Dummy)
        matches = [
            d
            for d in registrar_registration.registered_registrars()
            if d.registrar_cls is Dummy
        ]
        assert len(matches) == 1


class TestRegisterMcpTool:
    def test_registers_tool(self):
        @RegisterMcpTool(name="dummy_tool", description="d")
        async def dummy_tool(container):
            return "ok"

        names = [t.name for t in tool_registration.registered_tools()]
        assert "dummy_tool" in names

    def test_non_async_raises(self):
        with pytest.raises(TypeError, match="async function"):

            @RegisterMcpTool(name="sync_tool")
            def sync_tool(container):
                return "no"

    def test_missing_container_first_param_raises(self):
        with pytest.raises(TypeError, match="'container' as its first parameter"):

            @RegisterMcpTool(name="bad_tool")
            async def bad_tool(agent_id):
                return "no"

    def test_duplicate_name_different_fn_raises(self):
        @RegisterMcpTool(name="dupe_tool")
        async def first(container):
            return "1"

        with pytest.raises(ValueError, match="already registered"):

            @RegisterMcpTool(name="dupe_tool")
            async def second(container):
                return "2"


class TestBuildRegistrars:
    def test_resolves_extra_deps_by_provider_name(self):
        registrar_registration._reset_registry_for_tests()

        @RegisterMcpRegistrar(extra_deps=("prompt_registry",))
        class NeedsRegistry(McpRegistrar):
            def __init__(self, prompt_registry):
                self.prompt_registry = prompt_registry

        registrars = bootstrap.build_registrars(
            FakeContainer(prompt_registry="the-registry")
        )
        assert len(registrars) == 1
        assert registrars[0].prompt_registry == "the-registry"

    def test_missing_provider_raises_configuration_error(self):
        registrar_registration._reset_registry_for_tests()

        @RegisterMcpRegistrar(extra_deps=("missing_dep",))
        class NeedsMissing(McpRegistrar):
            def __init__(self, missing_dep):
                self.missing_dep = missing_dep

        with pytest.raises(ConfigurationError) as exc_info:
            bootstrap.build_registrars(FakeContainer())
        assert "missing_dep" in exc_info.value.detail
        assert "NeedsMissing" in exc_info.value.detail


class TestDecoratedToolBinding:
    @pytest.mark.asyncio
    async def test_container_is_hidden_from_schema_and_injected(self):
        from fastmcp import Client, FastMCP

        from agent_lab.interface.mcp.decorated_tool_registrar import (
            DecoratedToolRegistrar,
        )

        tool_registration._reset_registry_for_tests()

        @RegisterMcpTool(name="echo_tool", description="d")
        async def echo_tool(container, value: str) -> str:
            return f"{container.tag}:{value}"

        class Sentinel:
            tag = "CONTAINER"

        mcp = FastMCP(name="test")
        DecoratedToolRegistrar().register_tools(mcp, Sentinel())

        async with Client(mcp) as client:
            tool = next(t for t in await client.list_tools() if t.name == "echo_tool")
            assert "container" not in tool.inputSchema.get("properties", {})
            assert "value" in tool.inputSchema.get("properties", {})
            result = await client.call_tool("echo_tool", {"value": "hi"})
            assert result.data == "CONTAINER:hi"

    def test_positional_name_matches_register_agent_convention(self):
        tool_registration._reset_registry_for_tests()

        @RegisterMcpTool("positional_tool")
        async def positional_tool(container) -> str:
            return "ok"

        names = [t.name for t in tool_registration.registered_tools()]
        assert names == ["positional_tool"]


class TestRegisterMcpPrompt:
    def test_registers_prompt(self):
        @RegisterMcpPrompt("dummy_prompt", description="d")
        def dummy_prompt() -> str:
            return "text"

        names = [p.name for p in prompt_registration.registered_prompts()]
        assert "dummy_prompt" in names

    def test_async_fn_raises(self):
        with pytest.raises(TypeError, match="synchronous function"):

            @RegisterMcpPrompt("async_prompt")
            async def async_prompt() -> str:
                return "no"

    def test_duplicate_name_different_fn_raises(self):
        @RegisterMcpPrompt("dupe_prompt")
        def first() -> str:
            return "1"

        with pytest.raises(ValueError, match="already registered"):

            @RegisterMcpPrompt("dupe_prompt")
            def second() -> str:
                return "2"

    def test_same_fn_reregistration_is_idempotent(self):
        def stable() -> str:
            return "x"

        RegisterMcpPrompt("stable_prompt")(stable)
        RegisterMcpPrompt("stable_prompt")(stable)
        matches = [
            p
            for p in prompt_registration.registered_prompts()
            if p.name == "stable_prompt"
        ]
        assert len(matches) == 1

    def test_tenancy_params_must_come_together(self):
        with pytest.raises(TypeError, match="together"):
            RegisterMcpPrompt("half_tenant", agent_type="my_agent")

        with pytest.raises(TypeError, match="together"):
            RegisterMcpPrompt("other_half", setting_key="some_key")


class TestDecoratedPromptTriple:
    """A decorated prompt must land on all three prompt surfaces at once:
    the shared PromptRegistry (read_prompt_mcp tool + prompt://{name}
    template), prompts/get, and a concrete prompt://<name> resource."""

    def _registrar(self, prompt_registry, resolver=None):
        from agent_lab.interface.mcp.decorated_prompt_registrar import (
            DecoratedPromptRegistrar,
        )

        return DecoratedPromptRegistrar(
            prompt_registry=prompt_registry,
            user_prompt_resolver=resolver or MagicMock(),
        )

    @pytest.mark.asyncio
    async def test_prompt_exposed_on_all_three_surfaces(self):
        from fastmcp import Client, FastMCP

        prompt_registration._reset_registry_for_tests()

        @RegisterMcpPrompt("code_review", description="Code review system prompt")
        def code_review(language: str = "python") -> str:
            return f"You are a {language} code reviewer."

        registry = PromptRegistry()
        registrar = self._registrar(registry)

        # Surface 1: PromptRegistry, populated at construction time.
        assert registry.names() == ["code_review"]
        assert registry.resolve("code_review", language="go") == (
            "You are a go code reviewer."
        )

        mcp = FastMCP(name="test")
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

        async with Client(mcp) as client:
            # Surface 2: prompts/get, arguments advertised from the signature.
            prompt = next(
                p for p in await client.list_prompts() if p.name == "code_review"
            )
            assert [a.name for a in prompt.arguments or []] == ["language"]
            result = await client.get_prompt("code_review", {"language": "go"})
            assert "go code reviewer" in result.messages[0].content.text

            # Surface 3: concrete resource, served with defaults.
            contents = await client.read_resource("prompt://code_review")
            assert contents[0].text == "You are a python code reviewer."

    def test_tenant_override_replaces_output_verbatim(self):
        prompt_registration._reset_registry_for_tests()

        @RegisterMcpPrompt(
            "greeting", agent_type="my_agent", setting_key="greeting_prompt"
        )
        def greeting() -> str:
            return "DEFAULT"

        resolver = MagicMock()
        resolver.resolve.return_value = "TENANT OVERRIDE"
        registry = PromptRegistry()
        self._registrar(registry, resolver)

        assert registry.resolve("greeting") == "TENANT OVERRIDE"
        resolver.resolve.assert_called_once_with(
            agent_type="my_agent",
            setting_key="greeting_prompt",
            default_template="DEFAULT",
        )

    def test_prompt_without_tenancy_skips_resolver(self):
        prompt_registration._reset_registry_for_tests()

        @RegisterMcpPrompt("plain")
        def plain() -> str:
            return "PLAIN"

        resolver = MagicMock()
        registry = PromptRegistry()
        self._registrar(registry, resolver)

        assert registry.resolve("plain") == "PLAIN"
        resolver.resolve.assert_not_called()

    def test_name_collision_with_existing_prompt_fails_fast(self):
        prompt_registration._reset_registry_for_tests()

        @RegisterMcpPrompt("taken")
        def taken() -> str:
            return "x"

        registry = PromptRegistry()
        registry.register("taken", lambda **_: "other")

        with pytest.raises(ValueError, match="already registered"):
            self._registrar(registry)
