"""Deep bake test: installs a baked project against the in-repo library.

Opt-in via ``-m cookiecutter_bake`` (deselected by default). Run standalone
with ``pytest --noconftest tests/template -m cookiecutter_bake`` to skip the
testcontainers boot — the baked smoke tests need no containers.
"""

import subprocess

import pytest

from tests.template.test_bake_structural import REPO_ROOT, bake


@pytest.mark.cookiecutter_bake
def test_baked_project_installs_and_boots_against_working_tree(tmp_path):
    root = bake(tmp_path, include_testcontainers=False)

    # Point the baked project at the working tree instead of the last PyPI
    # release, so this test catches template drift before it is published.
    with (root / "pyproject.toml").open("a") as pyproject:
        pyproject.write(
            "\n[tool.uv.sources]\n"
            f'btech-agent-lab = {{ path = "{REPO_ROOT}", editable = true }}\n'
        )

    subprocess.run(["uv", "sync", "--group", "test"], cwd=root, check=True)
    subprocess.run(
        ["uv", "run", "--group", "test", "pytest", "tests/unit", "-v"],
        cwd=root,
        check=True,
    )
