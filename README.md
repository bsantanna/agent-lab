# Agent-Lab

[![Continuous Integration](https://github.com/bsantanna/agent-lab/actions/workflows/build.yml/badge.svg)](https://github.com/bsantanna/agent-lab/actions/workflows/build.yml)
[![Docker Image](https://github.com/bsantanna/agent-lab/actions/workflows/docker-image.yml/badge.svg)](https://hub.docker.com/r/bsantanna/agent-lab)
[![SonarCloud Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=bsantanna_agent-lab&metric=alert_status)](https://sonarcloud.io/dashboard?id=bsantanna_agent-lab)

Tool for generating synthetic datasets from dialog sessions using REACT agents.

This project implements a REACT agent using a LangGraph workflow consisting of
three steps:

- **Preparation**: Utilizes the REACT system prompt to prepare for a given task
  by obtaining different sources of information, reasoning about the task, and
  considering multiple strategies to solve the given user message input.
- **Execution**: Uses REACT to address the given problem, taking into account
  the preparation phase.
- **Conclusion**: Employs REACT to perform self-reflection, score its own
  performance, and record improvement suggestions for fine-tuning purposes.

---

## Benefits

- **Efficiency**: Streamlines the process of task preparation, execution, and
  self-reflection.
- **Customization**: Allows for configurable system prompts to tailor the
  workflow to specific needs.
- **Data Collection**: Facilitates the collection of dialog sessions for further
  analysis and fine-tuning.

---

## Features

- Configurable system prompts
- Query endpoint for performing workflow iteration steps
- Dataset endpoint for downloading dialog sessions in JSONL format for
  fine-tuning purposes

---

## Development Guide

To get started quickly and easily with this project, please refer to our
comprehensive [Development Guide](DEV_GUIDE.md). It provides step-by-step
instructions for setting up your environment, running the application,
and contributing to the project. Happy coding!

---

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md)
file for
more details.
