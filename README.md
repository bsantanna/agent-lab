# Agent-Lab

Tool for generating synthetic datasets from dialog sessions using REACT agents.

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

Access the API at: [http://127.0.0.1:18000](http://127.0.0.1:8000)

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

## 🤝 Contributing

We appreciate the support from the community and welcome any help to improve this project. If you encounter any issues or have suggestions for enhancements, please report them by creating an issue on our [GitHub Issues](https://github.com/bsantanna/agent-lab/issues) page.

To contribute to the project, follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Activate the pre-commit hooks by running `pre-commit install`, make your changes, and commit them with clear and concise messages.
4. Ensure your changes pass the pre-commit hooks and achieve at least 80% test coverage in SonarQube.
5. Push your changes to your forked repository.
6. Create a Pull Request (PR) to the `main` branch of the original repository.

We will review your PR and provide feedback. Thank you for your contributions and support!


---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE.md] file for more details.
