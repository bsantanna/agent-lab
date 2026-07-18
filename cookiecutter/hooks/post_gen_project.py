"""Applies the toggle deletion matrix.

Runs with the working directory already inside the generated project.
Each toggle owns a disjoint set of paths — no rule depends on another
toggle's value, with one documented exception: docker-image.yml requires
both include_release_pipeline and include_docker, so both rules remove it
(remove() tolerates already-deleted paths). String comparison (instead of
bare Jinja booleans) keeps this file valid Python before rendering, so the
host repo's check-ast / ruff hooks can parse it.
"""

import shutil
from pathlib import Path

INCLUDE_DOCKER = "{{ cookiecutter.include_docker }}" == "True"
INCLUDE_GITHUB_ACTIONS = "{{ cookiecutter.include_github_actions }}" == "True"
INCLUDE_TESTCONTAINERS = "{{ cookiecutter.include_testcontainers }}" == "True"
INCLUDE_CLAUDE_PLUGIN = "{{ cookiecutter.include_claude_plugin }}" == "True"
INCLUDE_RELEASE_PIPELINE = "{{ cookiecutter.include_release_pipeline }}" == "True"

PACKAGE_NAME = "{{ cookiecutter.package_name }}"


def remove(*relative_paths: str) -> None:
    for relative_path in relative_paths:
        target = Path(relative_path)
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


if not INCLUDE_DOCKER:
    remove(
        "docker",
        "compose.yml",
        "config-docker.yml",
        f"{PACKAGE_NAME}/agents/react_agent",
        ".github/workflows/docker-image.yml",
    )

if not INCLUDE_GITHUB_ACTIONS:
    remove(".github")

if not INCLUDE_TESTCONTAINERS:
    remove("tests/integration")

if not INCLUDE_CLAUDE_PLUGIN:
    remove(".claude-plugin", "plugins")

if not INCLUDE_RELEASE_PIPELINE:
    remove(
        ".github/workflows/release.yml",
        ".github/workflows/docker-image.yml",
    )

print(f"Generated {PACKAGE_NAME} — see README.md to get started.")
