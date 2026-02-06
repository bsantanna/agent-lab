# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent-Lab is a cloud-native LLM Agent Development and Testing Toolkit built with Python 3.12, FastAPI, LangChain/LangGraph, and PostgreSQL. It provides a platform for building, testing, and deploying autonomous agents and multi-agent systems.

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires PostgreSQL, Redis, and services from config-dev.yml)
make reset                  # Cleans docker compose deployment

# Run with Docker Compose (includes all infrastructure)
make run                    # runs: docker compose -f compose-grafana.yml up --build

# Lint
make lint                   # runs: python -m flake8 .

# Run all tests (spins up testcontainers: Postgres, Redis, Keycloak, Ollama, Vault, CDP)
make test                   # runs: pytest --cov=app --cov-report=xml

# Run a single test file
pytest tests/integration/test_agents_endpoint.py

# Run a single test
pytest tests/integration/test_agents_endpoint.py::TestAgentsEndpoints::test_create_agent

# Pre-commit hooks (flake8, ruff, ruff-format, full test suite)
pre-commit install
pre-commit run --all-files
```

## Configuration

Environment selection is driven by environment variables checked in `app/core/container.py`:
- `DEVELOPING=1` → `config-dev.yml` (local dev, auth disabled)
- `TESTING=1` → `config-test.yml` (testcontainers ports on 1xxxx)
- `DOCKER=1` → `config-docker.yml` (docker compose, main development environment, you default to this setup)
- None set → Vault-based production config


## Architecture

**Clean Architecture** with four layers:

- **Interface** (`app/interface/api/`) — FastAPI routers + MCP server endpoints
- **Services** (`app/services/`) — Business logic, agent implementations
- **Domain** (`app/domain/`) — SQLAlchemy models, repository interfaces, exceptions
- **Infrastructure** (`app/infrastructure/`) — Database, auth (Keycloak), metrics (OpenTelemetry)

**Dependency Injection** via `dependency-injector` library. All wiring is in `app/core/container.py` — this is the single source of truth for how services, repositories, and agents are composed.

**Entry point**: `app/main.py` — `create_app()` factory builds the FastAPI app with auth, routers, MCP, tracing, and middleware.

## Agent System

Agents are registered in `app/services/agent_types/registry.py` with string keys mapping to agent instances. The hierarchy:

```
AgentBase (ABC)
  └── WorkflowAgentBase — LangGraph workflow support
       ├── AdaptiveRagAgent — Adaptive retrieval with routing
       ├── ReactRagAgent — ReAct pattern with RAG tools
       ├── VisionDocumentAgent — Multi-modal document processing
       ├── VoiceMemosAgent variants — Audio transcription/analysis
       ├── WebAgentBase — Browser automation (browser-use)
       │    └── SupervisedWorkflowAgentBase — Multi-agent coordination
       │         └── CoordinatorPlannerSupervisorAgent
       └── TestEchoAgent — Simple echo for testing
```

Each agent implements:
- `create_default_settings(agent_id, schema)` — Initialize settings (prompts, params)
- `get_input_params(message_request, schema)` — Parse incoming message
- `process_message(message_request, schema)` — Main execution entry point
- `get_workflow_builder(agent_id)` — Build LangGraph StateGraph (for WorkflowAgentBase)

Agent settings are stored as key-value pairs in the database and support Jinja2 templates for prompts.

## Database Architecture

Three PostgreSQL databases:
- **Main** — Relational data (agents, settings, integrations, LLMs, messages, attachments)
- **Vectors** — PgVector extension for embeddings/RAG (`app/infrastructure/database/vectors.py`)
- **Checkpoints** — LangGraph state persistence (`app/infrastructure/database/checkpoints.py`)

Redis is used for task notification pub/sub.

## Testing

**Integration tests** (`tests/integration/`) use testcontainers (session-scoped) that start PostgreSQL (pgvector), Redis, Keycloak, Ollama (bge-m3), Vault, and headless Chrome. Tests use FastAPI's `TestClient` with Keycloak bearer tokens obtained per-test via the `set_access_token` fixture.

**Simulation tests** (`tests/simulation/`) use `langwatch-scenario` for agent behavior testing with LLM judges. These have a 60-second throttle between tests. Marked with `@pytest.mark.agent_test`.

The PgVector database is pre-loaded from `tests/integration/pgvector_dump.sql.gz` for consistent test data.

## Adding a New Agent Type

1. Create a new directory under `app/services/agent_types/<name>/`
2. Implement agent class extending `WorkflowAgentBase` (or appropriate base)
3. Register in `app/services/agent_types/registry.py`
4. Add DI wiring in `app/core/container.py` (factory provider + registry constructor arg)

## Linting Rules

- **flake8**: ignores E203, E501, W201, W503
- **ruff**: auto-fix enabled, ruff-format for formatting
- Max line length is not enforced (E501 ignored)

## Key Dependencies

LangChain/LangGraph for agent orchestration, FastAPI for REST API, `fastapi-mcp` for MCP server, `dependency-injector` for DI, `testcontainers` for integration tests, `langwatch-scenario` for simulation tests, `browser-use` for web automation agents.

## Notebooks

Jupyter notebooks for prototyping agents and workflows are in the `notebooks/` directory. These notebooks are used by the developer to debug and prototype code changes and new features.

## Development Lifecycle

1. Run `make reset` to reset development environment
2. Run `make run` to start services using docker compose
3. When a new feature is introduced, a new integration test should be added to `tests/integration/` that tests the new feature end-to-end using the FastAPI TestClient and testcontainers environment. For agent behavior testing, a new simulation test should be added to `tests/simulation/` using `langwatch-scenario`.
4. A developer manually tests changes using `curl` pointing to `http://localhost:18000`, curl queries examples are handy and should be given as example.
