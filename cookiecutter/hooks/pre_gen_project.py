"""Validates cookiecutter inputs before the project directory is created.

Cookiecutter renders this file with Jinja before executing it, so the
template variables below are interpolated as string literals.
"""

import keyword
import re
import sys

PROJECT_SLUG = "{{ cookiecutter.project_slug }}"
PACKAGE_NAME = "{{ cookiecutter.package_name }}"
AGENT_LAB_VERSION = "{{ cookiecutter.agent_lab_version }}"
INCLUDE_DOCKER = "{{ cookiecutter.include_docker }}" == "True"
INCLUDE_GITHUB_ACTIONS = "{{ cookiecutter.include_github_actions }}" == "True"
INCLUDE_RELEASE_PIPELINE = "{{ cookiecutter.include_release_pipeline }}" == "True"
INCLUDE_AKS_GITOPS = "{{ cookiecutter.include_aks_gitops }}" == "True"
AUTH_ENABLED = "{{ cookiecutter.auth_enabled }}" == "True"

# Names that would shadow the framework package or the generated project's
# own test-suite convention.
RESERVED_NAMES = {"agent_lab", "btech_agent_lab", "test", "tests"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", PROJECT_SLUG):
    fail(
        f"project_slug '{PROJECT_SLUG}' is invalid: use lowercase letters, "
        "digits and single hyphens, starting with a letter."
    )

if not PACKAGE_NAME.isidentifier() or keyword.iskeyword(PACKAGE_NAME):
    fail(f"package_name '{PACKAGE_NAME}' is not a valid Python package name.")

if PACKAGE_NAME in RESERVED_NAMES:
    fail(
        f"package_name '{PACKAGE_NAME}' collides with a reserved name "
        f"({sorted(RESERVED_NAMES)}); choose a different project_name."
    )

if not re.match(r"^\d+\.\d+\.\d+$", AGENT_LAB_VERSION):
    fail(
        f"agent_lab_version '{AGENT_LAB_VERSION}' must be a plain semantic "
        "version (e.g. '1.10.0') — the dependency range is built in "
        "pyproject.toml."
    )

if INCLUDE_RELEASE_PIPELINE and not INCLUDE_GITHUB_ACTIONS:
    fail(
        "include_release_pipeline requires include_github_actions: release.yml "
        "is triggered by the CI workflow completing and lives in .github/."
    )

if INCLUDE_AKS_GITOPS and not INCLUDE_DOCKER:
    fail(
        "include_aks_gitops requires include_docker: the gitops deployment "
        "runs the app image built from docker/app/Dockerfile."
    )

if AUTH_ENABLED and not INCLUDE_AKS_GITOPS:
    fail(
        "auth_enabled requires include_aks_gitops: the auth_* values are only "
        "wired into Vault app_secrets by terraform/aks/03_vault_config."
    )
