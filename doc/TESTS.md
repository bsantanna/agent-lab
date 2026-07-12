<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Integration tests</h3>

---

Agent-Lab provides a set of integration tests to ensure the functionality and reliability of the system over time and adapt to changes on libraries and AI services used in the project. These tests are designed to cover various aspects of the application, including interactions with external services, database operations, vector search, and API endpoints.

The main configuration file for integration tests is located at `tests/conftest.py`, which contains the necessary settings and parameters for running the tests. This file can be customized to suit your testing environment.

**Note:** Integration tests perform real calls to external services, so they may incur costs depending on the services used. It is recommended to run these tests in a controlled environment and monitor usage.

---

## Running Integration Tests

### Install Dependencies

- Docker or another container runtime.
- TestContainers Python library for managing Docker containers during tests.

Please refer to [Developer's Guide](DEV_GUIDE.md) for instructions on setting up the environment and installing dependencies.

### Run Tests
Run integration tests using the following command:

```bash
make test
```

---

## Agent Simulations

End-to-end agent simulations live in `tests/simulation/` and call live LLM providers. They are marked with `agent_test` and deselected by default; run them with:

```bash
make test_simulations
```

Three complementary tracks share the agent bootstrap helpers, judge, and the dataset definitions versioned under `tests/simulation/datasets/`:

- `tests/simulation/scenario/` — conversational simulations using the [langwatch-scenario](https://github.com/langwatch/scenario) framework (user simulator + judge agent).
- `tests/simulation/langfuse/` — dataset-driven experiments using [Langfuse](https://langfuse.com/) datasets. Each run syncs the dataset definitions, invokes the agent per dataset item, scores the output with a client-side LLM-as-judge, and records the run and scores in Langfuse for comparison over time. These tests skip automatically when `LANGFUSE_BASE_URL` (or the deprecated `LANGFUSE_HOST`), `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are not set.
- `tests/simulation/langwatch/` — the same dataset-driven experiments mirrored to [LangWatch](https://langwatch.ai/) via `langwatch.experiment`, logging the judge score per item. All definitions are synced idempotently into a single consolidated `simulations` dataset (a `dataset` column identifies the source definition) because the LangWatch free plan allows at most 3 datasets per project. These tests skip automatically when `LANGWATCH_ENDPOINT` and `LANGWATCH_API_KEY` are not set.

Running `uv run python scripts/setup_simulation_evals.py` mirrors the dataset definitions to every configured platform and provisions the Langfuse server-side evaluation setup (visible in the Langfuse Evaluations section): an LLM connection for the judge model, a `simulation_llm_as_judge` evaluator, and one evaluation rule per simulation dataset that scores every new experiment run. The script is idempotent and safe to re-run.

Both tracks use the same judge model configuration:

| Environment variable | Default | Purpose |
|---|---|---|
| `SIMULATION_JUDGE_MODEL` | `openai/gpt-5-nano` | litellm model id used by the LLM-as-judge |
| `SIMULATION_JUDGE_API_BASE` | provider default | custom OpenAI API compatible endpoint for the judge model |
| `SIMULATION_JUDGE_API_KEY` | provider default | API key for the custom endpoint |

The agents under test (and the scenario user simulator) run on a default LLM served by any OpenAI API compatible endpoint (e.g. a LAN inference server), provisioned per test by `tests/simulation/common/llm_factory.py`. The only exception is the voice memos agent, which stays on OpenAI because it needs audio chat input. Embeddings are unaffected: they keep using the `EMBEDDINGS_ENDPOINT` fallback (the test Ollama container serving `bge-m3`), matching the pgvector dump. The endpoint must support tool calling / structured output for the supervisor-based suites (browser automation, supervisor):

| Environment variable | Default | Purpose |
|---|---|---|
| `SIMULATION_LLM_MODEL` | none (required) | model tag executing the simulations (e.g. `qwen3:30b`) |
| `SIMULATION_LLM_API_BASE` | none (required) | OpenAI API compatible endpoint serving the model |
| `SIMULATION_LLM_API_KEY` | `dummy-key` | API key, if the endpoint requires one |
