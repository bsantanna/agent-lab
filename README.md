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
- [Overview](#overview)
- [Project Principles](#project-principles)
- [Key Features](#key-features)
- [MCP Server](#mcp-server)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

---

## What is Agent-Lab?

Agent-Lab is a cloud-native toolkit for building, testing, and deploying LLM-powered autonomous agents. Think of it as a platform where you wire up different AI agent types (RAG, browser automation, voice memos, vision, multi-agent supervisors) and interact with them via a REST API.

It features relational persistence with PostgreSQL, secure secrets management using Vault, observability through OpenTelemetry, and PgVector for vector storage and similarity search.

---

## Overview

**Tech stack:** Python 3.12, FastAPI, LangChain/LangGraph, PostgreSQL (3 databases: relational, vectors via pgvector, LangGraph checkpoints), Redis for pub/sub, Keycloak for auth, Docker Compose for orchestration.

**Architecture** — Clean Architecture with Dependency Injection:
- **Interface** — FastAPI routers + MCP server
- **Services** — Business logic, agent implementations
- **Domain** — SQLAlchemy models, repository interfaces
- **Infrastructure** — DB, auth, metrics (OpenTelemetry)

All wiring lives in `app/core/container.py` via `dependency-injector`.

**Agent system** — Agents extend `WorkflowAgentBase` (which uses LangGraph state graphs). Each agent type lives under `app/services/agent_types/` and is registered in a registry. The hierarchy goes from simple (echo, adaptive RAG) to complex (coordinator-planner-supervisor multi-agent). Agents process messages, have configurable settings (Jinja2-templated prompts), and persist state in the checkpoints database.

**Testing** — Two layers:
- **Integration tests** spin up real infrastructure via testcontainers (Postgres, Redis, Keycloak, Ollama, headless Chrome).
- **Simulation tests** use `langwatch-scenario` with LLM judges to evaluate agent behavior end-to-end.

**Deployment** — Ships with Helm charts (`charts/`) for Kubernetes and Terraform scripts (`terraform/`) for provisioning cloud infrastructure including databases, auth realms, and secrets. See [Setup guide](doc/SETUP.md) for details.

---

## Project Principles

- Give researchers and developers everything they need to build, test, and experiment with LLM agents, with ready-to-use reference implementations.
- Expose an MCP server for agent discovery, conversation history, and agent-to-agent communication.
- Ship with integration and simulation test suites so every agent change is validated automatically.
- Provide full observability through logs, metrics, and traces for explainability and evaluation.
- Make it easy to create new custom agents by extending base classes and registering them in the agent registry.
- Run anywhere with a cloud-native architecture built for containerized deployment and horizontal scaling.

---

## Key Features

- **REST API**: Manage integrations with AI suppliers, LLMs settings, agents, and conversation histories with our [REST API](doc/REST_API.md).
- **MCP Server**: Utilize the [Model Control Protocol (MCP) server](doc/MCP.md) for agent discovery, dialog history, and agent-to-agent communication.
- **Observability**: Obtain detailed insights through logs, metrics, and traces powered by [OpenTelemetry](doc/OTEL.md).
  - Includes reference implementations for [Grafana](doc/otel/GRAFANA.md) and [OpenSearch Dashboards](doc/otel/OPENSEARCH.md).
- **Cloud-Native**: Optimized for cloud environments with Docker, Kubernetes, and [Terraform scripts](doc/SETUP.md) for streamlined deployment.
- **Relational Persistence**: Store data reliably using PostgreSQL to support the [entity domain model](doc/DOMAIN.md) for prompts, agent-specific settings, conversations, and more.
- **Secrets Management**: Securely store and retrieve secrets with [Vault](doc/VAULT.md).
- **Vector Storage and Search**: Efficiently manage vector data using PgVector for similarity search and retrieval.
- **Agent Memory**: Using PostgreSQL checkpointer to store and retrieve agent memory, enabling agents to maintain context across interactions.
- **Integration Testing**: Ensure reliability and correctness with a comprehensive [integration test suite](doc/TESTS.md).

---

## MCP Server

Agent-Lab features a MCP Server that allows agent discovery (`get_agent_list` tool), dialog history (`get_message_list` tool) and agent-to-agent communication (`post_message` tool).

The following example shows MCP Server discovering and obtaining dialog history of a [supervised coder agent](/notebooks/05_test_agent_type-multiagent-coder.ipynb) instance:

<div align="center">

![Claude Desktop Demo](doc/claude_demo.gif)

</div>

Please refer to [MCP guide](doc/MCP.md) for more details.


**Note**: Claude Desktop is used only for demonstration purposes. This project is not affiliated with Anthropic AI.

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
