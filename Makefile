run:
	python -m app

test:
	pytest --cov=app --cov-report=xml

lint:
	python -m flake8 .
