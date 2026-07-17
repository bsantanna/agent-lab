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
