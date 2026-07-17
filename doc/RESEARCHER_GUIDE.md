<h2 align="center"><a href="https://github.com/btech-software/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Researcher Guide</h3>

---

## Introduction

Welcome — this guide is for AI researchers and developers who want to explore, reproduce, and extend experiments in Agent-Lab. If you write Python, use Jupyter, and think in terms of experiments, agents, and pipelines, you'll feel at home here.

Agent-Lab is a modular framework for building and experimenting with autonomous agents and multi-agent systems. It provides reusable components (agent types, tools, connectors, and data pipelines) and a collection of Jupyter notebooks with step-by-step examples so you can get productive quickly.

Goals of this guide:

- Give a quick path to running the example notebooks in `/notebooks`.
- Explain the project structure and where core concepts live.
- Show how to run experiments, adapt components, and add new agent behaviours.
- Cover testing, metrics, and practical tips for reproducible research.

Audience: AI developers and researchers familiar with Python and Jupyter notebooks. Knowledge of LLMs, retrieval-augmented generation (RAG), and container basics is helpful but not required.

---

## Quickstart (run the examples)

This project keeps its notebooks in the `notebooks/` folder. Each notebook is an executable showcase of an agent type or integration.

Minimum requirements:

- Python 3.12+ (see `pyproject.toml` for exact dependency pins)
- A working Jupyter environment (JupyterLab or Notebook)
- Optional: local Docker for infra (OpenSearch/Grafana) if you plan to run end-to-end integrations

Quick steps to get started locally, working in a clone of the repository with [uv](https://docs.astral.sh/uv/):

1. Sync the environment (creates a virtualenv and installs the runtime plus notebook
   dependencies):

   uv sync --group notebooks

2. Start Jupyter in the repository root:

   jupyter lab

3. Open the `notebooks/` folder in Jupyter and run the notebooks prefixed with a number (e.g., `01_setup_embeddings_service.ipynb`). Start with `01_...` and progress through the ones that interest you.

Notes:
- Notebooks are written to be mostly self-contained. Some notebooks demonstrate integrations requiring API keys or local services. Each notebook contains a header explaining any environment variables or external services required.
- If you prefer running individual scripts, see `agent_lab/` and `agent_lab/core/` for runnable modules and small CLI entry points.
- To experiment against Agent-Lab from your own project instead of the repository, `pip install btech-agent-lab` and assemble the app with `create_app()`; see the [Developer's Guide](DEV_GUIDE.md#extending-the-framework).

---

## Project layout — quick tour

High level folders to know as a researcher:

- `notebooks/` — Collection of interactive examples that demonstrate agent types, evaluation, and integrations. This is the best place to start.
- `agent_lab/` — Application package containing all source code, organized as follows:
  - `agent_lab/core/` — Core runtime components (container, shared abstractions).
  - `agent_lab/domain/` — Domain models and repository interfaces used by agents.
  - `agent_lab/services/` — Agent implementations and business logic.
  - `agent_lab/infrastructure/` — Implementations for storage, auth, metrics, and other infra concerns.
  - `agent_lab/interface/api/` — HTTP API definitions and adapters.
- `tests/` — Unit and integration tests. See `tests/integration` for heavier examples.
- `doc/` — Project documentation and guides (this file lives here).

Understanding these layers helps you pick where to change behavior: examples live in `notebooks`, core logic in `agent_lab/core` and `agent_lab/domain`, and infra adapters in `agent_lab/infrastructure`.

---

## Notebooks — the primary learning path

The `notebooks/` directory was created to guide exploration. Notebooks are short, focused experiments. Typical progression:

1. `01_setup_embeddings_service.ipynb` — Start here to configure and validate your embeddings provider. Many agents rely on embeddings for retrieval; this notebook shows how the project expects embedding services to behave.
2. `02_test_agent_type-adaptive_rag.ipynb` — Demonstrates an adaptive RAG agent that chooses retrieval strategies.
3. `03_test_agent_type-react_rag.ipynb` — Shows an agent using the ReAct pattern with retrieval and tool usage.
4. `04_test_agent_type-vision_document.ipynb` — Example mixing computer vision and document retrieval.
5. `05_test_agent_type-multiagent-coder.ipynb` — Multi-agent collaboration for code tasks.
6. `06_test_agent_type-multiagent-researcher.ipynb` — A multi-agent setup oriented to research workflows.
7. `07_test_agent_type-multiagent-browser.ipynb` — Agents that interact with web-browsing tools.
8. `08_test_agent_type-multiagent-voice-assistant.ipynb` and variants — Voice agent examples and pipeline setups.

Each notebook contains:
- A short description of the experiment objective.
- Environment variables and secrets required (e.g., API keys).
- Small helper functions and reproducible seeds where applicable.
- Visualization or printed outputs to inspect agent decisions and metrics.

Pro tip: run notebooks in order for an incremental learning curve. Use smaller datasets and sample sizes while iterating to keep runs fast.

---

## Core concepts and components

Key abstractions you'll encounter in the codebase:

- Agent: the central actor implementing a strategy (RAG, ReAct, multi-agent coordination, etc.). Look under `agent_lab/services/agent_types/` for agents and `agent_lab/main.py` for the entrypoint.
- Tools: discrete abilities an agent can call (search, web browsing, code execution, TTS/ASR). Tools are implemented as adapters in `agent_lab/infrastructure/` or `agent_lab/interface/`.
- Container: a lightweight orchestration object (see `agent_lab/core/container.py`) used to compose agents with their dependencies for experiments.
- Repositories: domain data access interfaces in `agent_lab/domain/repositories` (persistence, retrieval).
- Models: data classes and DTOs for passing structured data between components (`agent_lab/domain/models.py`).

When you want to modify behavior, decide whether the change is:
- Experimental (change in a notebook only)
- Architectural (change in `core`/`domain`/`services`)
- Integration-level (adapter in `infrastructure`)

Favor small, testable changes and add or update a notebook to show the new behavior.

---

## Running experiments and capturing results

Notebooks often print intermediate steps. For more robust experiments:

- Use deterministic seeds where randomness matters.
- Log structured events (the project includes a basic logging setup; see `logs/app.log` and `infrastructure/metrics`).
- Capture metrics relevant to your research question — accuracy, latency, token usage, tool-call counts, and human evaluation results.

For repeatable runs consider:
- Exporting notebook cells to scripts using `jupyter nbconvert --to script` and then running them as experiments in CI or on compute nodes.
- Dockerizing the experiment environment (a `Dockerfile` exists in the repo) so dependencies and runtime are pinned.

---

## Extending Agent-Lab: practical recipes

1. Add a new agent type:
   - Create the agent class under `agent_lab/services/agent_types/` following existing patterns, and decorate it with `@discoverable_agent("your_type")` so it is discovered.
   - Implement any new tool interfaces under `agent_lab/infrastructure/`.
   - Add a notebook in `notebooks/` that mounts your agent through `agent_lab/core/container` and exercises it with a small scenario.

2. Swap an embeddings provider:
   - Implement a compatible adapter in `infrastructure` that matches the project's expected `embed(text)` interface.
   - Update `01_setup_embeddings_service.ipynb` or create a small notebook to validate embeddings and downstream retrieval quality.

3. Add a retrieval store or vector DB:
   - Implement repository methods in `domain/repositories` and an adapter in `infrastructure/database`.
   - Provide a small data loader notebook (or script) to seed the store and a query notebook demonstrating retrieval.

Design tip: keep adapter interfaces narrow and test them in isolation with small unit tests.

---

## Testing and CI

- Unit tests live under `tests/`. Run them with pytest:

   pytest -q

- Integration tests that require external services are grouped under `tests/integration` and usually need local services or mocks. Use `pytest -k integration` or the integration folder directly.

- When you change core behavior, add a unit test and a short notebook demonstrating the change for reproducibility and review.

---

## Metrics, observability, and instrumentation

The repository contains basic hooks for metrics and logs (see `infrastructure/metrics` and `logs/`). For research experiments, capture:

- Performance metrics: latency, throughput, tokens consumed per request.
- Accuracy/utility metrics: retrieval precision, downstream task success, human preference scores.
- Behavior metrics: tool call frequency, agent decision traces.

Export logs and metrics to CSV/JSON for analysis and plotting in notebooks.

---

## Troubleshooting common issues

- Notebook stalls on an external call: check API key env vars and service availability. Many notebooks print required env var names at the top.
- Dependency conflicts: recreate the environment from scratch with `uv sync --group notebooks`.
- Long runs: reduce dataset size and sampling parameters. Add failsafes for timeouts when calling LLM APIs.

If you hit obscure errors, search the repo for the failing symbol and run the relevant unit tests to localize the issue.

---

## Reproducibility checklist (short)

- Pin your Python environment (virtualenv, pip freeze or use `pyproject.toml`).
- Record seeds and config files (`config-dev.yml`, `config-test.yml`).
- Save the notebook checkpoint and any output artifacts (CSV/JSON) alongside your experiment.

---

## Where to go next (suggested exploration path)

1. Run `01_setup_embeddings_service.ipynb` to validate embeddings.
2. Run `02_...` and `03_...` to see RAG and ReAct patterns in action.
3. Modify a notebook to swap an embeddings provider or a different LLM backend and observe behavior changes.
4. Add a small unit test for your change and open a PR with the updated notebook and test.

---

## Acknowledgements and references

- See `doc/` for architecture diagrams and auxiliary guides (MCP, OTEL, etc.).
- The notebooks include in-line references to papers and patterns used (RAG, ReAct, multi-agent coordination).

---
