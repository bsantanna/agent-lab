cleanup:
	@rm agent_lab.db 2>/dev/null || true
	@rm temp* 2>/dev/null || true

sync_simulation_evals:
	uv run python scripts/setup_simulation_evals.py

scenario_simulation: sync_simulation_evals
	uv run pytest tests/simulation/scenario -m agent_test --timeout=1800; $(MAKE) cleanup

langwatch_simulation: sync_simulation_evals
	uv run pytest tests/simulation/langwatch -m agent_test --timeout=1800; $(MAKE) cleanup

langfuse_simulation: sync_simulation_evals
	uv run pytest tests/simulation/langfuse -m agent_test --timeout=1800; $(MAKE) cleanup

test:
	uv run pytest --cov=app --cov-report=xml; $(MAKE) cleanup

test_simulations: sync_simulation_evals
	uv run pytest tests/simulation -m agent_test --timeout=1800; $(MAKE) cleanup

lint:
	uv run python -m flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
	uv run python -m flake8 app tests --count --exit-zero --statistics
