# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

Built on [Agent-Lab](https://github.com/btech-software/agent-lab) (`btech-agent-lab`).

## Quickstart

```bash
uv lock            # required once before docker builds (uv sync --frozen needs it)
uv sync --group dev --group test
cp .env.example .env

make lint
make test_unit     # no-container smoke tests: app boots, examples registered
```

Run locally (needs Postgres, Redis, and Vault reachable per `config-dev.yml`):

```bash
DEVELOPING=1 uv run uvicorn {{ cookiecutter.package_name }}.main:app --reload
```
{% if cookiecutter.include_docker %}
Or run the full stack in containers:

```bash
docker compose up --build -d
curl http://localhost:18000/status/liveness
```
{% endif %}

## Project layout

- `{{ cookiecutter.package_name }}/main.py` — the composition root: `create_app()` scans only this
  project's packages, so none of Agent-Lab's built-in agents/tools are exposed.
  Add `"agent_lab.services.agent_types"` / `"agent_lab.interface.mcp"` to
  `scan_packages` to opt back in.
- `{{ cookiecutter.package_name }}/core/container.py` — add your own dependency-injection providers
  here; reference them from agents via `extra_deps`.
- `{{ cookiecutter.package_name }}/agents/` — one example echo agent (`@discoverable_agent`){% if cookiecutter.include_docker %} and a
  single-node ReAct workflow agent whose checkpointed state stores a
  chain-of-thought per turn{% endif %}.
- `{{ cookiecutter.package_name }}/mcp/` — one example MCP tool and prompt, exposed at `/mcp`.

{% if cookiecutter.include_docker %}
## Prompt templates

Agent prompts stored in agent settings are Jinja2 templates rendered at
runtime, e.g. {% raw %}`Today is {{ CURRENT_TIME }}.`{% endraw %} — see
`agents/react_agent/default_execution_system_prompt.txt`.
{% endif %}
{% if cookiecutter.include_testcontainers %}
## Integration tests

```bash
make test_integration   # boots Postgres, Redis, and Vault via testcontainers
```
{% endif %}
{% if cookiecutter.include_claude_plugin %}
## Claude Code plugin marketplace

`.claude-plugin/marketplace.json` publishes the plugins under `plugins/` as a
Claude Code marketplace. The included `{{ cookiecutter.project_slug }}-dev`
plugin ships a guided feature-development workflow (`/{{ cookiecutter.project_slug }}-dev`); replace or
extend it with your own plugins. Once the repo is on GitHub:

```
/plugin marketplace add <your-org>/{{ cookiecutter.project_slug }}
/plugin install {{ cookiecutter.project_slug }}-dev@{{ cookiecutter.project_slug }}
```
{% endif %}
{% if cookiecutter.include_release_pipeline %}
## Releases

`.github/workflows/release.yml` runs [python-semantic-release](https://python-semantic-release.readthedocs.io/)
after each successful CI run on `main`: commit messages following
[Conventional Commits](https://www.conventionalcommits.org/) drive the version
bump, and every version-bearing file listed in `[tool.semantic_release]`
`version_variables` (in `pyproject.toml`) is updated in the release commit.

Setup: add a `GH_TOKEN` repository secret — a personal access token with push
access to `main` — so the release commit and tag can be pushed back and
trigger downstream workflows.
{%- if cookiecutter.include_docker %}
After each release, `docker-image.yml` builds a multi-arch image, pushes it to
`ghcr.io/{{ cookiecutter.github_repository }}`, and signs it with cosign.
{%- endif %}
{% endif %}
{% if cookiecutter.include_aks_gitops %}
## AKS + GitOps deployment

`terraform/aks/` provisions an AKS cluster (with Azure Key Vault-backed Vault
auto-unseal), installs Flux, and syncs the `gitops/` manifests: traefik,
cert-manager, CloudNativePG, Redis, Vault, and this app — deployed from
`ghcr.io/{{ cookiecutter.github_repository }}`, served over HTTPS at the
configured `app_hostname` (with a headless-Chrome CDP sidecar for browser
agents), and configured entirely from Vault via its ServiceAccount. Vault
initialization is automated; the root token lands in the Azure Key Vault. See
[docs/one-time-setup.md](docs/one-time-setup.md) for the bootstrap steps.
{% endif %}
