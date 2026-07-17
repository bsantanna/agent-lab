---
name: runtime-verifying
description: Runtime verification recipes for agent-lab — booting the app without live infrastructure and verifying the cookiecutter template end-to-end by baking, installing against the working tree, and driving the generated server.
---

# Verifying agent-lab changes at runtime

## Boot the app without containers

`create_app()` needs no live infrastructure — engines are lazy. From the repo
root (config-test.yml has `auth.enabled: false` and valid placeholder URLs):

```bash
TESTING=1 uv run python -c "import agent_lab.main; print(agent_lab.main.app.title)"
TESTING=1 uv run uvicorn agent_lab.main:app --port 18111
curl http://localhost:18111/status/liveness            # {"status":"ok"}
```

- DI endpoints require an `Authorization: Bearer <anything>` header even with
  auth disabled (`Depends(HTTPBearer())` on every route) — without it: 401.
- `/agents/types` is DI-injected but DB-free: the fastest probe that container
  wiring works. DB-backed endpoints (e.g. `/integrations/list`) 500 without
  live postgres/vault — expected.
- MCP (stateless): `POST /mcp` with headers `Content-Type: application/json`,
  `Accept: application/json, text/event-stream`, JSON-RPC body
  `{"jsonrpc":"2.0","id":1,"method":"tools/list"}` (also `prompts/list`,
  `prompts/get`).

## Verify the cookiecutter template

Fast structural matrix + opt-in deep bake (`--noconftest` skips the
testcontainers session boot, which is otherwise autouse for all of tests/):

```bash
uv run --group test pytest --noconftest tests/template                       # 8-combo matrix
uv run --group test pytest --noconftest tests/template -m cookiecutter_bake  # bake + uv sync vs working tree + baked smoke tests
```

Manual end-to-end (the real user flow):

```bash
uvx cookiecutter . --directory cookiecutter --no-input -o /tmp/bake
cd /tmp/bake/my-agent-app
printf '\n[tool.uv.sources]\nbtech-agent-lab = { path = "<repo>", editable = true }\n' >> pyproject.toml
uv sync --group test && TESTING=1 uv run uvicorn my_agent_app.main:app --port 18111
```

Then drive `/status/liveness`, `/agents/types` (dummy bearer → only the
project's namespaced agents), and MCP `tools/list` / `prompts/get`.

## Gotchas

- Baked-tree formatting is enforced: the structural test runs
  `ruff format --check` on every bake — template .py payload edits must be
  ruff-format-clean *after rendering* (short package names collapse
  multi-line calls; keep them single-line in the template).
- `wiring_config` is NOT inherited by Container subclasses;
  `create_app()` compensates via `wire_framework_modules()`. If a subclass
  consumer 500s with `'Provide' object has no attribute ...`, wiring is the
  cause.
