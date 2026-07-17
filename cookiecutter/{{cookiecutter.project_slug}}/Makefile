lint:
	uv run ruff check {{ cookiecutter.package_name }} tests
	uv run ruff format --check {{ cookiecutter.package_name }} tests

test_unit:
	uv run --group test pytest tests/unit
{%- if cookiecutter.include_testcontainers %}

test_integration:
	uv run --group test pytest tests/integration

test: test_unit test_integration
{%- else %}

test: test_unit
{%- endif %}
