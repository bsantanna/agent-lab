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
- [What is Agent-Lab?](#what-is-agent-lab)
- [Project Goals](#project-goals)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

---

## What is Agent-Lab?

Agent-Lab is a robust toolkit engineered for the development and thorough testing of Large Language Model (LLM) agents. It offers key features designed to streamline the process, including a REST API for managing interactions, relational persistence with PostgreSQL for data storage, and secure secrets management using Vault. In addition, Agent-Lab emphasizes observability through OpenTelemetry for detailed insights and leverages PgVector for effective vector storage and search, ultimately providing a comprehensive platform for building and evaluating LLM-powered agents.

---

## Project Goals

- Support researchers and developers with a comprehensive toolkit for developing, testing, and experimenting with LLM agents, including example implementations.
- Provide an MCP server interface for agent discovery, dialog history, and agent-to-agent communication.
- Offer integration testing support to ensure quality assurance.
- Deliver observability for responsible AI explainability and agent evaluation.
- Leverage a cloud-native architecture for seamless deployment and scalability.

---

## Key Features

- **REST API**: Easily manage integrations with LLMs, agents, and conversation histories with our [REST API](doc/REST_API.md).
- **MCP Server**: Utilize the [Model Control Protocol (MCP) server](doc/MCP.md) for agent discovery, dialog history, and agent-to-agent communication.
- **Cloud-Native**: Optimized for cloud environments with Docker, Kubernetes, and [Helm charts](doc/CHARTS.md) for streamlined deployment.
- **Relational Persistence**: Store data reliably using PostgreSQL to support the [entity domain model](doc/DOMAIN.md) for prompts, agent-specific settings, conversations, and more.
- **Secrets Management**: Securely store and retrieve secrets with [Vault](doc/VAULT.md).
- **ETL Pipelines**: Integrate external data sources and LLMs using [Apache Airflow](doc/ETL.md) to orchestrate batch processing and data preparation tasks.
- **Observability**: Obtain detailed insights through logs, metrics, and traces powered by [OpenTelemetry](doc/OTEL.md).
  - Includes reference implementations for [Grafana](doc/otel/GRAFANA.md) and [OpenSearch Dashboards](doc/otel/OPENSEARCH.md).
- **Vector Storage and Search**: Efficiently manage vector data using PgVector for similarity search and retrieval.
- **Unit Testing**: Ensure reliability and correctness with a comprehensive [integration test suite](doc/TESTS.md).

---

## Getting Started

Agent-Lab is designed for ease of setup and use, whether you're a developer building LLM agents or a researcher experimenting with agentic workflows.

Documentation in this repository is divided into two main sections:

- **Developer's Guide**: Tailored for developers who want to customize Agent-Lab or build agentic workflows. It includes setup instructions and development practices. Please refer to our [developer's guide](doc/DEV_GUIDE.md).
- **Researcher's Guide**: Provides detailed instructions for researchers on setting up and using Agent-Lab, including how to run the MCP server, manage agents, conduct experiments, tune prompts, and prototype new agents. Please refer to our [researcher's guide](doc/RESEARCHER_GUIDE.md).

Please consult these guides for detailed instructions on getting started with Agent-Lab.

---

## Contributing

Community support is greatly appreciated. If you encounter any issues or have suggestions for enhancements, please report them by creating an issue on our [GitHub Issues](https://github.com/bsantanna/agent-lab/issues) page.

Refer to our [developer's guide](doc/DEV_GUIDE.md) for instructions on how to contribute to the project.

---

## License

This project is licensed under the MIT License. See the [LICENSE](doc/LICENSE.md) file for details.
