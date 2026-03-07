---
name: software-engineering
description: Use when the user asks about architecture, running, testing, linting, or building the project, or about code conventions.
---

# Software Engineering

## Architecture

### Dependency Injection

All wiring is in `app/core/container.py` using `dependency-injector`. The `Container` class declares every service, repository, and agent as a provider. FastAPI endpoints receive dependencies via container wiring (configured in `wiring_config`). To add a new service, register it as a provider in the Container and add the endpoint module to wiring.

### Agent System

Agents are the core abstraction. The class hierarchy:

```
AgentBase (ABC)
├── WorkflowAgentBase          # LangGraph state graph + checkpointer
│   ├── ContactSupportAgentBase
│   └── WebAgentBase           # Adds browser automation + web search tools
│       └── SupervisedWorkflowAgentBase  # Coordinator → Planner → Supervisor pattern
└── TestEchoAgent              # Simple echo agent for testing
```

Key patterns:
- **AgentBase** (`app/services/agent_types/base.py`): Defines `create_default_settings`, `get_input_params`, `process_message` abstract methods. Also houses `AgentUtils` which bundles all shared dependencies (services, repos, config).
- **AgentRegistry** (`app/services/agent_types/registry.py`): Maps string type keys (e.g. `"test_echo"`) to agent instances. To register a new agent: add it to the registry dict, create a factory in `Container`, and wire it into `AgentRegistry.__init__`.
- **WorkflowAgentBase**: Provides `get_workflow_builder()` → compiles LangGraph `StateGraph` with a PostgreSQL checkpointer. Handles `process_message` by invoking the graph and publishing progress via Redis (`TaskNotificationService`).
- **SupervisedWorkflowAgentBase**: Implements multi-role orchestration with abstract methods for `get_coordinator`, `get_planner`, `get_supervisor`, `get_reporter`.

### LLM Integration

`AgentBase.get_chat_model()` dynamically selects the LangChain chat model class based on `integration.integration_type`:
- `openai_api_v1` → `ChatOpenAI`
- `anthropic_api_v1` → `ChatAnthropic`
- `xai_api_v1` → `ChatXAI`
- `ollama_api_v1` / default → `ChatOllama`

API keys and endpoints are stored in Vault under `integration_{id}` and retrieved via `get_integration_credentials()`.

### Request Flow

1. HTTP request hits a FastAPI router in `app/interface/api/`
2. Router calls a service (e.g., `MessageService.process_message`)
3. Service resolves the agent type via `AgentRegistry.get_agent()`
4. Agent builds a LangGraph workflow, invokes it with PostgreSQL checkpointing
5. Progress updates publish to Redis; final result returns as JSON

### Database Schema

Three PostgreSQL databases:
- **agent_lab**: Relational data (agents, agent_settings, messages, attachments, language_models, language_model_settings, integrations) via SQLAlchemy
- **agent_lab_vectors**: pgvector embeddings via `DocumentRepository`
- **agent_lab_checkpoints**: LangGraph workflow state via `GraphPersistenceFactory`

### Observability

OpenTelemetry is configured in `app/infrastructure/metrics/tracer.py`. Instrumented: FastAPI, HTTPx, LangChain, SQLAlchemy, Psycopg. Exports via OTLP to a collector that feeds Prometheus (metrics), Loki (logs), Tempo (traces), and Grafana (dashboards). Config in `otel/`.

---

## Common Commands

### Backend

**Important:** All Python commands must use the `agent-lab` conda environment: `conda run -n agent-lab <command>`

```bash
# Run the app locally (requires Postgres, Redis, Vault running)
make run

# Run all tests (spins up testcontainers: Postgres, Redis, Vault, Keycloak, Ollama, chromedp)
make test

# Run a single test file
pytest tests/integration/test_status_endpoint.py

# Run a single test by name
pytest tests/integration/test_status_endpoint.py -k "test_name"

# Lint
make lint

# Format (via ruff)
ruff format .
ruff check --fix .
```

### Backend Debugging

```bash
# View live app container logs (useful for debugging API errors)
docker compose logs -f app

# Rebuild and restart the app container after backend code changes
docker compose build app && docker compose up -d app
```

**Note:** The backend runs inside a Docker container (`compose.yml`). Local changes to Python files in `app/` are NOT reflected until the container is rebuilt. Always rebuild after modifying backend code.

## REST API Design

Follow the **Richardson Maturity Model** (Level 3) when designing or modifying API endpoints.

### HTTP Method Selection

Choose the method based on the operation's semantics, not implementation convenience:

| Method | Use When | Safe | Idempotent | Cacheable |
|--------|----------|------|------------|-----------|
| `GET` | Retrieving data (reads, queries, searches, bulk lookups) | Yes | Yes | Yes |
| `POST` | Creating resources or triggering non-idempotent operations | No | No | No |
| `PUT` | Full replacement of a resource | No | Yes | No |
| `PATCH` | Partial update of a resource | No | No | No |
| `DELETE` | Removing a resource | No | Yes | No |

**Key rule:** If a request is **safe** (no side effects) and **idempotent** (same result on repeated calls), it MUST be a GET. This enables browser/CDN caching via `Cache-Control` headers. POST requests are never cached by browsers regardless of cache headers.

### Query Parameters vs Request Body

- **GET endpoints**: Pass filters via query parameters. For lists, use comma-separated values (e.g., `?key_tickers=AAPL,MSFT,NVDA`).
- **POST/PUT/PATCH endpoints**: Use JSON request body for resource creation/mutation.
- **URL path parameters**: Use for resource identifiers (e.g., `/stats_close/{index_name}/{key_ticker}`).

### Caching

- Use the `cache_control(max_age)` dependency from `app/interface/api/cache_control.py`.
- Read-heavy, infrequently-changing data (e.g., market caps, EOD stats): `cache_control(86400)` (24h).
- Frequently-changing data (e.g., news, real-time prices): `cache_control(3600)` (1h) or less.
- Caching only works with GET — never rely on cache headers for POST endpoints.

### Resource Naming

- Use **nouns** for resources, not verbs: `/markets/stats_close`, not `/markets/get_stats`.
- Use **snake_case** for path segments and query params (matching Python conventions).
- Use plural when returning collections: `/markets/news`, `/markets/indicators`.

### Validation

- Path/query params are validated via `_validate_index_name()` regex in `endpoints.py`.
- Never expose internal patterns (e.g., ES wildcards `*`) through the API — resolve them server-side or use aliases.

---

## Code Conventions

- **Linting**: flake8 (ignores E203, E501, W201, W503) + ruff (auto-fix + format). Both run as pre-commit hooks.
- **Pre-commit hooks**: Also run `make test` as a local hook on every commit — tests must pass before commits succeed.
- **Config files**: YAML-based (`config-*.yml`), loaded conditionally by env var in `Container`.
- **Agent prompts**: Use Jinja2 templates stored in agent settings, rendered via `AgentBase.parse_prompt_template()`.
- **Versioning**: Managed by `python-semantic-release`.
- **Testing**: pytest with testcontainers — tests spin up real Postgres, Redis, Vault, Keycloak, Ollama, and chromedp containers. The `conftest.py` session fixture manages container lifecycle.

