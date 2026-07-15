import threading

from agent_lab.domain.exceptions.base import ConfigurationError
from agent_lab.services.agent_types import registration
from agent_lab.services.agent_types.base import AgentBase


class AgentRegistry:
    """Lazily instantiates @RegisterAgent-registered agents from the container.

    Each agent's declared ``extra_deps`` are resolved by provider attribute
    name off the live (possibly downstream-subclassed) container instance.
    """

    def __init__(self, container):
        self._container = container
        self._cache: dict = {}
        # Guards first-time instantiation so concurrent requests for the same
        # not-yet-cached agent type build it once, matching the thread-safety
        # the previous dependency-injector Singleton provided.
        self._lock = threading.Lock()

    def get_agent_types(self) -> list:
        return registration.registered_types()

    def get_agent(self, agent_type: str) -> AgentBase:
        if agent_type not in self._cache:
            with self._lock:
                if agent_type not in self._cache:
                    self._cache[agent_type] = self._instantiate(agent_type)
        return self._cache[agent_type]

    def _instantiate(self, agent_type: str) -> AgentBase:
        descriptor = registration.get_descriptor(agent_type)
        kwargs = {"agent_utils": self._container.agent_utils()}
        for dep_name in descriptor.extra_deps:
            provider = getattr(self._container, dep_name, None)
            if provider is None:
                raise ConfigurationError(
                    f"agent '{agent_type}' declares extra dependency '{dep_name}' "
                    f"but {type(self._container).__name__} has no such provider"
                )
            kwargs[dep_name] = provider()
        return descriptor.agent_cls(**kwargs)
