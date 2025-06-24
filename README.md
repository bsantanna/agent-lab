<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">LLM Agent Development and Testing Toolkit</h3>

<div align="center">

[![Continuous Integration](https://github.com/bsantanna/agent-lab/actions/workflows/build.yml/badge.svg)](https://github.com/bsantanna/agent-lab/actions/workflows/build.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=bsantanna_agent-lab&metric=alert_status)](https://sonarcloud.io/dashboard?id=bsantanna_agent-lab)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=bsantanna_agent-lab&metric=coverage)](https://sonarcloud.io/component_measures?metric=coverage&selected=bsantanna_agent-lab%3Aapp&id=bsantanna_agent-lab)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009485.svg?logo=fastapi&logoColor=white)](#key-features)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](doc/LICENSE.md)

</div>

---

### Table of Contents
- [What's Agent-Lab?](#whats-agent-lab)
- [Project Goals](#project-goals)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

---

## What's Agent-Lab?

Agent-Lab is a robust toolkit specifically engineered for the development and rigorous testing of Large Language Model (LLM) agents. It highlights key features that streamline this process, including a REST API for managing interactions, relational persistence with PostgreSQL for data storage, and secure secrets management using Vault. Furthermore, Agent-Lab emphasizes observability through OpenTelemetry for detailed insights and leverages PgVector for efficient vector storage and search, ultimately offering a comprehensive platform for building and evaluating LLM-powered agents.

---

## Project Goals

- Deliver a comprehensive toolkit for the development, testing, and experimentation of LLM agents including example implementations.
- Offer MCP server interface for agent discovery, dialog history, and agent-to-agent communication.
- Offer first-class integration testing support to ensure quality assurance.
- Support Observability for responsible AI explainability and agent evaluation.
- Leverage a cloud-native architecture for seamless deployment and scalability.

---

## Key Features:

- **REST API**: Effortlessly manage integrations with LLMs, agents, and conversation history.
- **MCP Server**: A Model Control Protocol (MCP) server for agent discovery, dialog history, and agent-to-agent communication.
- **Cloud-Native**: Optimized for cloud environments with Docker, Kubernetes, and [Helm charts](doc/CHARTS.md) for streamlined deployment.
- **Relational Persistence**: Reliable data storage using PostgreSQL for prompts, agent-specific settings, and conversations.
- **Secrets Management**: Securely store and retrieve secrets with [Vault](doc/VAULT.md).
- **ETL Pipelines**: Integrates external data sources and LLMs using [Apache Airflow](doc/DAGs.md) for orchestrating batch processing and data-preparation tasks.
- **Observability**: Gain detailed insights with logs, metrics, and traces powered by [OpenTelemetry](doc/OTEL.md).
  - Includes reference implementations for [Grafana](doc/otel/GRAFANA.md) and [OpenSearch Dashboards](doc/otel/OPENSEARCH.md).
- **Vector Storage and Search**: Efficiently handle vector data with PgVector for similarity search and retrieval.
- **Unit Testing**: Ensure reliability and correctness with a comprehensive [integration test suite](doc/TESTS.md).

---

## Getting Started

...

---

## Contributing

We appreciate the support from the community and welcome any help to improve this project. If you encounter any issues or have suggestions for enhancements, please report them by creating an issue on our [GitHub Issues](https://github.com/bsantanna/agent-lab/issues) page.

To contribute to the project, follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Activate the pre-commit hooks by running `pre-commit install`, make your
   changes, and commit them with clear and concise messages.
4. Ensure your changes pass the pre-commit hooks and achieve at least 80% test
   coverage in SonarQube.
5. Push your changes to your forked repository.
6. Create a Pull Request (PR) to the `main` branch of the original repository.

We will review your PR and provide feedback. Thank you for your contributions and support!

---

## License

This project is licensed under the MIT License. See the [LICENSE](doc/LICENSE.md) file for more details.
