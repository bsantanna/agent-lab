from dataclasses import dataclass

from typing_extensions import Sequence


@dataclass(frozen=True)
class AgentDescriptor:
    agent_type: str
    agent_cls: type
    extra_deps: tuple

    # extra_deps entries name both the container provider attribute and the
    # agent constructor kwarg — the same name-equality convention the
    # containers already use for hand-wired factories.


_registry: dict = {}


def discoverable_agent(agent_type: str, *, extra_deps: Sequence[str] = ()):
    """Registers an AgentBase subclass under ``agent_type``.

    Decoration only records metadata; instantiation happens lazily in
    ``AgentRegistry`` once a live container exists, resolving each name in
    ``extra_deps`` as a container provider passed as a constructor kwarg.
    """

    def decorator(cls):
        from agent_lab.services.agent_types.base import AgentBase

        if not issubclass(cls, AgentBase):
            raise TypeError(
                f"@discoverable_agent requires an AgentBase subclass, got {cls!r}"
            )
        existing = _registry.get(agent_type)
        if existing is not None and existing.agent_cls is not cls:
            raise ValueError(
                f"agent_type '{agent_type}' already registered by {existing.agent_cls!r}"
            )
        _registry[agent_type] = AgentDescriptor(agent_type, cls, tuple(extra_deps))
        return cls

    return decorator


def registered_types() -> list:
    return sorted(_registry)


def is_registered(agent_type: str) -> bool:
    return agent_type in _registry


def get_descriptor(agent_type: str) -> AgentDescriptor:
    return _registry[agent_type]


def _reset_registry_for_tests() -> None:
    _registry.clear()
