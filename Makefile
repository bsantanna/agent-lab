reset:
	docker compose -f compose-grafana.yml stop
	docker compose -f compose-grafana.yml rm -f

run:
	docker compose -f compose-grafana.yml up --build

test:
	rm agent_lab.db || true
	pytest --cov=app --cov-report=xml
	rm temp*

lint:
	python -m flake8 .
