import threading

from agent_lab.core.extra_deps import resolve_extra_deps
from agent_lab.services.agent_types import registration
from agent_lab.services.agent_types.base import AgentBase


class AgentRegistry:
    """Lazily instantiates @discoverable_agent-registered agents from the container.

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
        kwargs.update(
            resolve_extra_deps(
                self._container,
                descriptor.extra_deps,
                owner=f"agent '{agent_type}'",
            )
        )
        return descriptor.agent_cls(**kwargs)
