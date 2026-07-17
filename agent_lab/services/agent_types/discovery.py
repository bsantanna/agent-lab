import importlib
import pkgutil
from importlib import metadata as importlib_metadata

from typing_extensions import Sequence

ENTRY_POINT_GROUP = "agent_lab.agents"


def scan_packages(package_names: Sequence[str]) -> None:
    """Imports every module under each package so discoverable decorators fire.

    The single discovery entry point for all capability decorators —
    @discoverable_agent, @discoverable_mcp_tool, @discoverable_mcp_prompt,
    @discoverable_mcp_registrar. Accepts plain modules too (imported as-is).
    Re-imports are no-ops via ``sys.modules``, so scanning is idempotent
    across repeated create_app calls.
    """
    for name in package_names:
        package = importlib.import_module(name)
        if not hasattr(package, "__path__"):
            continue
        prefix = package.__name__ + "."
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, prefix):
            importlib.import_module(module_name)


def load_entry_point_agents(group: str = ENTRY_POINT_GROUP) -> None:
    """Imports agent modules advertised by installed packages.

    A package opts in via ``[project.entry-points."agent_lab.agents"]``;
    loading the entry point imports its target, firing @discoverable_agent.
    """
    for entry_point in importlib_metadata.entry_points(group=group):
        entry_point.load()
