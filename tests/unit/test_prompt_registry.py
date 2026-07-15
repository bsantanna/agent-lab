import pytest

from app.interface.mcp.prompt_registry import PromptRegistry


class TestPromptRegistry:
    def test_register_and_resolve(self):
        registry = PromptRegistry()
        registry.register("p1", lambda: "rendered-prompt")
        assert registry.resolve("p1") == "rendered-prompt"

    def test_duplicate_registration_raises(self):
        registry = PromptRegistry()
        registry.register("p1", lambda: "a")
        with pytest.raises(ValueError, match="already registered"):
            registry.register("p1", lambda: "b")

    def test_unknown_name_raises_with_available_list(self):
        registry = PromptRegistry()
        registry.register("alpha", lambda: "")
        registry.register("beta", lambda: "")
        with pytest.raises(KeyError) as excinfo:
            registry.resolve("gamma")
        message = str(excinfo.value)
        assert "gamma" in message
        assert "alpha" in message
        assert "beta" in message

    def test_unknown_name_with_empty_registry(self):
        registry = PromptRegistry()
        with pytest.raises(KeyError, match="<none>"):
            registry.resolve("x")

    def test_names_returns_sorted_keys(self):
        registry = PromptRegistry()
        registry.register("beta", lambda: "")
        registry.register("alpha", lambda: "")
        assert registry.names() == ["alpha", "beta"]

    def test_resolve_forwards_params_to_resolver(self):
        registry = PromptRegistry()
        captured: dict = {}

        def resolver(**params):
            captured.update(params)
            return "ok"

        registry.register("p", resolver)
        assert registry.resolve("p", deep_search_mode="true", current_time="t") == "ok"
        assert captured == {"deep_search_mode": "true", "current_time": "t"}
