"""Reference application entrypoint.

Importing this module builds the standalone Agent-Lab app with every built-in
agent registered. Library consumers should import :func:`create_app` from
``agent_lab`` (or ``agent_lab.app_factory``) instead and pass their own
container, scan packages, and router mounts.
"""

from agent_lab.app_factory import create_app

app = create_app(scan_packages=["agent_lab.services.agent_types"])
