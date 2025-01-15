run:
	python -m app

test:
	rm agent_lab.db || true
	pytest --cov=app --cov-report=xml

lint:
	python -m flake8 .
