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

- Support researchers and developers with a comprehensive toolkit for the development, testing, and experimentation of LLM agents including example implementations.
- Offer MCP server interface for agent discovery, dialog history, and agent-to-agent communication.
- First-class integration testing support for quality assurance.
- Support observability for responsible AI explainability and agent evaluation.
- Leverage a cloud-native architecture for seamless deployment and scalability.

---

## Key Features:

- **REST API**: Effortlessly manage integrations with LLMs, agents, and conversation history.
- **MCP Server**: A [Model Control Protocol (MCP) server](doc/MCP.md) for agent discovery, dialog history, and agent-to-agent communication.
- **Cloud-Native**: Optimized for cloud environments with Docker, Kubernetes, and [Helm charts](doc/CHARTS.md) for streamlined deployment.
- **Relational Persistence**: Reliable data storage using PostgreSQL for [entity domain model](doc/DOMAIN.md) containing prompts, agent-specific settings, conversations...
- **Secrets Management**: Securely store and retrieve secrets with [Vault](doc/VAULT.md).
- **ETL Pipelines**: Integrates external data sources and LLMs using [Apache Airflow](doc/ETL.md) for orchestrating batch processing and data-preparation tasks.
- **Observability**: Gain detailed insights with logs, metrics, and traces powered by [OpenTelemetry](doc/OTEL.md).
  - Includes reference implementations for [Grafana](doc/otel/GRAFANA.md) and [OpenSearch Dashboards](doc/otel/OPENSEARCH.md).
- **Vector Storage and Search**: Efficiently handle vector data with PgVector for similarity search and retrieval.
- **Unit Testing**: Ensure reliability and correctness with a comprehensive [integration test suite](doc/TESTS.md).

---

## Getting Started

The toolkit is designed to be straightforward to set up and use, whether you are a developer looking to build LLM agents or a researcher wanting to experiment with agentic workflows.

Documentation in this repository is divided into two main sections:

- **Developer's Guide**: This section is tailored for developers who want to customize Agent-Lab or build agentic workflows. It includes setup instructions and development practices. Please refer to our [developer's guide](doc/DEV_GUIDE.md).
- **Researcher's Guide**: This section provides detailed instructions for researchers on how to set up and use Agent-Lab, including how to run the MCP server, manage agents, perform experiments, tune prompts, and prototype new agents. Please refer to our [researcher's guide](doc/RESEARCHER_GUIDE.md).

Please refer to these guides for detailed instructions on how to get started with Agent-Lab.

---

## Contributing

We appreciate the support from the community and welcome any help to improve this project. If you encounter any issues or have suggestions for enhancements, please report them by creating an issue on our [GitHub Issues](https://github.com/bsantanna/agent-lab/issues) page.

Please refer to our [developer's guide](doc/DEV_GUIDE.md) for instructions on how to contribute to the project.

---

## License

This project is licensed under the MIT License. See the [LICENSE](doc/LICENSE.md) file for more details.
