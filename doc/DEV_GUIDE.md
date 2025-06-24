<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Development Guide</h3>

---

The goal of this document is to provide a quick introduction for developers.

## Setup

### Install dependencies

After setting up python environment, install the dependencies with pip package manager. It is recommended to use a virtual environment to avoid conflicts with other projects.:

```bash
pip install -r requirements.txt
```

Make sure **Docker** or another container runtime is installed and running as the application uses docker for integration tests and docker compose for application dependencies.

### Copy the example environment file
Copy the example environment file to `.env` and adjust the settings as needed:

```bash
cp .env.example .env
```

This file contains api keys for various AI suppliers.

### Run tests

Run the tests to make sure everything is working as expected:

```bash
make test
```

### Initialize pre-commit

If you plan to contribute to the codebase, it is recommended to install the pre-commit hooks:

```bash
pre-commit install
```

---

## Running the Application

### Start the application with Docker Compose

At this time, there are two pre-configured docker compose files:

- `compose-graphana.yaml`: Starts the application with Grafana for observability.
- `compose-opensearch.yaml`: Starts the application with OpenSearch Dashboards for observability.

The following example starts application with Grafana:

```bash
docker compose -f compose-graphana.yaml up --build
```

The following example starts application with OpenSearch Dashboards:

```bash
docker compose -f compose-opensearch.yaml up --build
```

After the application is started, you can access the API at [http://localhost:18000](http://localhost:18000).

Observability dashboards can be accessed at:
- Grafana: [http://localhost:3000](http://localhost:3000) (default credentials: `admin`/`admin`)
- OpenSearch Dashboards: [http://localhost:5601](http://localhost:5601)

### Start the application with Uvicorn

For development and debugging with an IDE, you can run the application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

Access the interactive documentation (OpenAPI):

- Swagger UI: [http://localhost:8000/docs](http://127.0.0.1:8000/docs)

---

