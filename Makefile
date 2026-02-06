cleanup:
	rm agent_lab.db || true
	rm temp* || true

reset:
	docker compose -f compose-grafana.yml stop
	docker compose -f compose-grafana.yml rm -f

run:
	docker compose -f compose-grafana.yml up --build

test:
	pytest --cov=app --cov-report=xml; $(MAKE) cleanup

lint:
	python -m flake8 .
