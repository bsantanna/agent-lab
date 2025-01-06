# Agent Lab

API for Generating Synthetic Datasets from Dialog Sessions Using REACT Agents.

This project implements a REACT agent using a LangGraph workflow consisting of three steps:

- **Preparation**: Utilizes the REACT system prompt to prepare for a given task by obtaining different sources of information, reasoning about the task, and considering multiple strategies to solve the given user message input.
- **Execution**: Uses REACT to address the given problem, taking into account the preparation phase.
- **Conclusion**: Employs REACT to perform self-reflection, score its own performance, and record improvement suggestions for fine-tuning purposes.

---

## Features

- Configurable system prompts
- Query endpoint for performing workflow iteration steps
- Dataset endpoint for downloading dialog sessions in JSONL format for fine-tuning purposes

---

## Benefits

- **Efficiency**: Streamlines the process of task preparation, execution, and self-reflection.
- **Customization**: Allows for configurable system prompts to tailor the workflow to specific needs.
- **Data Collection**: Facilitates the collection of dialog sessions for further analysis and fine-tuning.


---

## 🚀 Quick Start

Execute the following command to build container images:

```bash
docker compose build
```

After building the images, run the following command to start the application:

```bash
docker compose up
```

Access the API at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ⚙️ Development Environment Setup

### Create a virtual environment

Create a virtual environment to isolate the dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install dependencies

After activating the virtual environment, install the dependencies:

```bash
pip install -r requirements.txt
```

### Run tests

After installing the dependencies, run the tests to make sure everything is working as expected:

```bash
make test
```

### Initialize pre-commit

If you plan to contribute to the codebase, it is recommended to install the pre-commit hooks:

```bash
pre-commit install
```

---

## 🏃 Running the Application

### Locally

```bash
uvicorn app.main:app --reload
```

---

## 📚 API Documentation

Access the interactive documentation (OpenAPI):

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📂 Project Structure

```plaintext
/
├── alembic
├── app
│   ├── application
│   ├── core
│   ├── domain
│   ├── infrastructure
│   ├── interfaces
│   ├── middleware
├── tests
    ├── integration
    ├── unit
```

---
