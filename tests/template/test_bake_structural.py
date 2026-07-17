"""Bake-matrix tests for the cookiecutter template in cookiecutter/.

No containers or network needed — safe to run standalone with
``pytest --noconftest tests/template`` to skip the testcontainers boot.
"""

import itertools
import json
import subprocess
import tomllib
from pathlib import Path

import pytest
from cookiecutter.exceptions import FailedHookException
from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).parents[2]
TEMPLATE_DIR = str(REPO_ROOT / "cookiecutter")
TOGGLES = ("include_docker", "include_github_actions", "include_testcontainers")


def bake(output_dir: Path, **extra_context) -> Path:
    return Path(
        cookiecutter(
            TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context={"project_name": "Test App", **extra_context},
        )
    )


def toggle_combinations():
    for values in itertools.product([True, False], repeat=len(TOGGLES)):
        yield dict(zip(TOGGLES, values))


@pytest.mark.parametrize(
    "toggles",
    list(toggle_combinations()),
    ids=lambda toggles: "-".join(
        f"{name.removeprefix('include_')}={'on' if value else 'off'}"
        for name, value in toggles.items()
    ),
)
def test_bake_produces_expected_tree(tmp_path, toggles):
    root = bake(tmp_path, **toggles)

    assert (root / "docker").exists() == toggles["include_docker"]
    assert (root / "compose.yml").exists() == toggles["include_docker"]
    assert (root / "config-docker.yml").exists() == toggles["include_docker"]
    assert (root / "test_app" / "agents" / "react_agent").exists() == toggles[
        "include_docker"
    ]
    assert (root / ".github").exists() == toggles["include_github_actions"]
    assert (root / "tests" / "integration").exists() == toggles[
        "include_testcontainers"
    ]

    for py_file in root.rglob("*.py"):
        compile(py_file.read_text(), str(py_file), "exec")

    for rendered_file in root.rglob("*"):
        if rendered_file.is_file():
            assert "{{ cookiecutter" not in rendered_file.read_text(errors="ignore"), (
                f"unrendered template variable in {rendered_file}"
            )

    assert "[tool.uv.sources]" not in (root / "pyproject.toml").read_text()

    subprocess.run(["uv", "run", "ruff", "check", str(root)], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["uv", "run", "ruff", "format", "--check", str(root)],
        cwd=REPO_ROOT,
        check=True,
    )


def test_runtime_prompt_template_survives_bake(tmp_path):
    root = bake(tmp_path)
    prompt = (
        root
        / "test_app"
        / "agents"
        / "react_agent"
        / "default_execution_system_prompt.txt"
    ).read_text()
    assert "{{ CURRENT_TIME }}" in prompt


def test_pre_gen_rejects_reserved_package_name(tmp_path):
    with pytest.raises(FailedHookException):
        bake(tmp_path, project_name="Agent Lab")


def test_agent_lab_version_default_matches_library_version():
    pyproject_version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())[
        "project"
    ]["version"]
    template_version = json.loads(
        (REPO_ROOT / "cookiecutter" / "cookiecutter.json").read_text()
    )["agent_lab_version"]

    assert template_version == pyproject_version, (
        "cookiecutter.json's agent_lab_version default has drifted from "
        "pyproject.toml's version — update it (or verify the semantic-release "
        "version_variables substitution actually fired)."
    )
