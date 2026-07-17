# Agent-Lab project template

Cookiecutter template scaffolding a downstream application on the
`btech-agent-lab` library.

## Usage

```bash
uvx cookiecutter gh:btech-software/agent-lab --directory cookiecutter
```

Or from a local checkout:

```bash
uvx cookiecutter /path/to/agent-lab --directory cookiecutter
```

## Variables

| Variable | Default | Effect |
|---|---|---|
| `project_name` | `My Agent App` | Human-readable name; `project_slug` (kebab) and `package_name` (snake) derive from it |
| `agent_lab_version` | current release | Lower bound of the generated `btech-agent-lab>=X.Y.Z,<X+1.0.0` dependency range; bumped automatically by semantic-release |
| `include_docker` | `true` | `docker/`, `compose.yml`, `config-docker.yml`, and the ReAct workflow example agent |
| `include_github_actions` | `true` | `.github/workflows/ci.yml` (lint + tests) |
| `include_testcontainers` | `true` | `tests/integration/` harness (Postgres, Redis, Vault) |

## Maintenance invariants

- **`agents/__init__.py` and `mcp/__init__.py` in the payload must stay empty.**
  Capability discovery is import-driven (`scan_packages` walks and imports
  every submodule), so the toggle deletion matrix in
  `hooks/post_gen_project.py` stays trivially safe only while no `__init__.py`
  imports its siblings.
- **Each toggle owns a disjoint path set** in `post_gen_project.py` — never
  make one deletion rule depend on another toggle's value.
- **Runtime Jinja must not pass through cookiecutter's renderer.** Files
  containing runtime `{{ ... }}` templates (agent prompt files) are listed in
  `_copy_without_render` in `cookiecutter.json`; README snippets use
  `{% raw %}` blocks.
- **Template `.py` payload files are not valid Python before rendering** —
  they are excluded from the host repo's ruff/pre-commit AST hooks. The hooks
  in `hooks/` ARE valid Python (Jinja only inside string literals) and stay
  lint-clean.
- The bake matrix (all 8 toggle combinations) is tested in
  `tests/template/test_bake_structural.py`; a deeper opt-in test
  (`-m cookiecutter_bake`) installs a baked project against this repo's
  working tree and runs its smoke tests. Adding a new toggle means updating
  `cookiecutter.json`, the deletion matrix, and both tests.
- `agent_lab_version` in `cookiecutter.json` is listed in
  `[tool.semantic_release] version_variables`, and a consistency test asserts
  it matches `pyproject.toml`'s version.
