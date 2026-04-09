cleanup:
	rm agent_lab.db || true
	rm temp* || true

reset:
	docker compose -f compose-grafana.yml stop
	docker compose -f compose-grafana.yml rm -f

run:
	docker compose -f compose-grafana.yml up --build -d

test:
	uv run pytest --cov=app --cov-report=xml; $(MAKE) cleanup

lint:
	uv run python -m flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
	uv run python -m flake8 app tests --count --exit-zero --statistics
