from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Sequence


@dataclass(frozen=True)
class RegistrarDescriptor:
    registrar_cls: type
    extra_deps: tuple

    # extra_deps entries name both the container provider attribute and the
    # registrar constructor kwarg — the same name-equality convention used by
    # @RegisterAgent for agent extra dependencies.


_registry: dict = {}  # keyed by class, preserving decoration order


def RegisterMcpRegistrar(*, extra_deps: Sequence[str] = ()):
    """Registers an ``McpRegistrar`` subclass for MCP capability discovery.

    Decoration only records metadata; instantiation happens in
    ``bootstrap.build_registrars`` once a live container exists, resolving each
    name in ``extra_deps`` as a container provider passed as a constructor
    kwarg. Mirrors ``@RegisterAgent`` so downstream apps contribute registrars
    without editing the container.
    """

    def decorator(cls):
        from agent_lab.interface.mcp.registrar import McpRegistrar

        if not (isinstance(cls, type) and issubclass(cls, McpRegistrar)):
            raise TypeError(
                f"@RegisterMcpRegistrar requires an McpRegistrar subclass, got {cls!r}"
            )
        _registry[cls] = RegistrarDescriptor(cls, tuple(extra_deps))
        return cls

    return decorator


def registered_registrars() -> list:
    return list(_registry.values())


def _reset_registry_for_tests() -> None:
    _registry.clear()
