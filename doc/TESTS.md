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

Two complementary tracks share the agent bootstrap helpers in `tests/simulation/common/`:

- `tests/simulation/scenario/` — conversational simulations using the [langwatch-scenario](https://github.com/langwatch/scenario) framework (user simulator + judge agent).
- `tests/simulation/langfuse/` — dataset-driven experiments using [Langfuse](https://langfuse.com/) datasets. Dataset definitions are versioned under `tests/simulation/langfuse/datasets/` and synced idempotently to Langfuse on each run. Each run invokes the agent per dataset item, scores the output with a client-side LLM-as-judge, and records the run and scores in Langfuse for comparison over time. These tests skip automatically when `LANGFUSE_BASE_URL` (or the deprecated `LANGFUSE_HOST`), `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are not set.

Running `uv run python scripts/setup_langfuse_evals.py` additionally provisions the server-side evaluation setup (visible in the Langfuse Evaluations section): an LLM connection for the judge model, a `simulation_llm_as_judge` evaluator, and one evaluation rule per simulation dataset that scores every new experiment run. The script is idempotent and safe to re-run.

Both tracks use the same judge model configuration:

| Environment variable | Default | Purpose |
|---|---|---|
| `SIMULATION_JUDGE_MODEL` | `openai/gpt-5-nano` | litellm model id used by the user simulator and LLM-as-judge |
| `SIMULATION_JUDGE_API_BASE` | provider default | custom OpenAI API compatible endpoint for the judge model |
| `SIMULATION_JUDGE_API_KEY` | provider default | API key for the custom endpoint |
