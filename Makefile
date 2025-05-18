run:
	python -m app

test:
	rm agent_lab.db || true
	xvfb-run pytest --cov=app --cov-report=xml

lint:
	python -m flake8 .
