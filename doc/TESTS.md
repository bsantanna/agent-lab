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


