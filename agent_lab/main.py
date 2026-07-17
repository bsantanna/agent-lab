"""Reference application entrypoint.

Importing this module builds the standalone Agent-Lab app with every built-in
capability registered (``DEFAULT_SCAN_PACKAGES``). Library consumers should
import :func:`create_app` from ``agent_lab`` (or ``agent_lab.app_factory``)
instead and pass their own container, scan packages, and router mounts.
"""

from agent_lab.app_factory import create_app

app = create_app()
