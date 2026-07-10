"""Idempotently provision the simulation datasets and evaluators in Langfuse.

Reads every dataset definition under tests/simulation/langfuse/datasets and
creates or updates the corresponding Langfuse dataset and items. Also
provisions the server-side LLM-as-Judge setup so results appear in the
Evaluations section: an LLM connection for the judge model, one
'simulation_llm_as_judge' evaluator, and one evaluation rule per dataset
targeting its experiment runs. Safe to re-run: datasets are upserted by name,
items by id, the LLM connection by provider, and evaluators/rules are only
created when absent.

Usage:
    uv run python scripts/setup_langfuse_evals.py

Requires LANGFUSE_BASE_URL (or LANGFUSE_HOST), LANGFUSE_PUBLIC_KEY and
LANGFUSE_SECRET_KEY. The judge model follows SIMULATION_JUDGE_MODEL /
SIMULATION_JUDGE_API_BASE / SIMULATION_JUDGE_API_KEY.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langfuse import Langfuse  # noqa: E402
from langfuse.api.llm_connections import LlmAdapter  # noqa: E402
from langfuse.api.unstable.commons import (  # noqa: E402
    EvaluationRuleFilter_StringOptions,
    EvaluationRuleMapping,
    EvaluationRuleMappingSource,
    EvaluationRuleOptionsFilterOperator,
    EvaluationRuleTarget,
    EvaluatorModelConfig,
    EvaluatorOutputDataType,
    EvaluatorOutputDefinition_Numeric,
    EvaluatorOutputFieldDefinition,
    EvaluatorScope,
)
from langfuse.api.unstable.evaluation_rules import (  # noqa: E402
    CreateLlmAsJudgeEvaluationRuleRequest,
    LlmAsJudgeEvaluationRuleEvaluatorReference,
    LlmAsJudgeEvaluatorType,
)
from langfuse.api.unstable.evaluators import (  # noqa: E402
    CreateEvaluatorRequest_LlmAsJudge,
)

from tests.simulation.common.config import (  # noqa: E402
    JUDGE_API_BASE,
    JUDGE_API_KEY,
    JUDGE_MODEL,
)
from tests.simulation.langfuse.runner import (  # noqa: E402
    DATASETS_DIR,
    load_definition,
    sync_dataset,
)

EVALUATOR_NAME = "simulation_llm_as_judge"

# evaluator/rule creation preflights a live judge-model call server-side
PREFLIGHT_REQUEST_OPTIONS = {"timeout_in_seconds": 120}

EVALUATOR_PROMPT = """You are an impartial judge evaluating the response of an LLM agent.

User message:
{{input}}

Agent response:
{{output}}

Evaluation criteria:
{{expected_output}}

Rate between 0.0 and 1.0 how well the agent response satisfies all evaluation criteria.
"""


def parse_judge_model() -> tuple[str, str]:
    if "/" in JUDGE_MODEL:
        provider, model = JUDGE_MODEL.split("/", 1)
    else:
        provider, model = "openai", JUDGE_MODEL
    return provider, model


def sync_llm_connection(langfuse: Langfuse) -> bool:
    provider, model = parse_judge_model()
    secret_key = JUDGE_API_KEY or os.getenv(f"{provider.upper()}_API_KEY")
    if not secret_key:
        print(f"No API key found for judge provider '{provider}', skipping evaluators")
        return False

    adapter = LlmAdapter.ANTHROPIC if provider == "anthropic" else LlmAdapter.OPEN_AI
    kwargs = {"base_url": JUDGE_API_BASE} if JUDGE_API_BASE else {}
    langfuse.api.llm_connections.upsert(
        provider=provider,
        adapter=adapter,
        secret_key=secret_key,
        custom_models=[model],
        **kwargs,
    )
    print(f"Synced LLM connection '{provider}' (model '{model}')")
    return True


def ensure_evaluator(langfuse: Langfuse) -> None:
    evaluators = langfuse.api.unstable.evaluators.list(limit=100)
    for evaluator in evaluators.data:
        if evaluator.name == EVALUATOR_NAME and evaluator.scope == "project":
            print(f"Evaluator '{EVALUATOR_NAME}' already exists")
            return

    provider, model = parse_judge_model()
    langfuse.api.unstable.evaluators.create(
        request=CreateEvaluatorRequest_LlmAsJudge(
            name=EVALUATOR_NAME,
            prompt=EVALUATOR_PROMPT,
            output_definition=EvaluatorOutputDefinition_Numeric(
                data_type=EvaluatorOutputDataType.NUMERIC,
                reasoning=EvaluatorOutputFieldDefinition(
                    description="Explain why the score was assigned.",
                ),
                score=EvaluatorOutputFieldDefinition(
                    description="Score between 0.0 and 1.0 rating how well the "
                    "response meets all criteria.",
                ),
            ),
            model_config_=EvaluatorModelConfig(provider=provider, model=model),
        ),
        request_options=PREFLIGHT_REQUEST_OPTIONS,
    )
    print(f"Created evaluator '{EVALUATOR_NAME}'")


def ensure_evaluation_rules(langfuse: Langfuse, dataset_names: list) -> None:
    existing = {
        rule.name for rule in langfuse.api.unstable.evaluation_rules.list().data
    }
    for dataset_name in dataset_names:
        rule_name = f"{dataset_name}_judge"
        if rule_name in existing:
            print(f"Evaluation rule '{rule_name}' already exists")
            continue
        dataset = langfuse.api.datasets.get(dataset_name)
        langfuse.api.unstable.evaluation_rules.create(
            request=CreateLlmAsJudgeEvaluationRuleRequest(
                name=rule_name,
                evaluator=LlmAsJudgeEvaluationRuleEvaluatorReference(
                    name=EVALUATOR_NAME,
                    scope=EvaluatorScope.PROJECT,
                    type=LlmAsJudgeEvaluatorType.LLM_AS_JUDGE,
                ),
                target=EvaluationRuleTarget.EXPERIMENT,
                enabled=True,
                sampling=1.0,
                filter=[
                    EvaluationRuleFilter_StringOptions(
                        column="datasetId",
                        operator=EvaluationRuleOptionsFilterOperator.ANY_OF,
                        value=[dataset.id],
                    )
                ],
                mapping=[
                    EvaluationRuleMapping(
                        variable="input",
                        source=EvaluationRuleMappingSource.INPUT,
                    ),
                    EvaluationRuleMapping(
                        variable="output",
                        source=EvaluationRuleMappingSource.OUTPUT,
                    ),
                    EvaluationRuleMapping(
                        variable="expected_output",
                        source=EvaluationRuleMappingSource.EXPECTED_OUTPUT,
                    ),
                ],
            ),
            request_options=PREFLIGHT_REQUEST_OPTIONS,
        )
        print(f"Created evaluation rule '{rule_name}'")


def main() -> int:
    if not (
        (os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST"))
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    ):
        print(
            "Missing environment variables: LANGFUSE_BASE_URL (or LANGFUSE_HOST), "
            "LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY"
        )
        return 1

    langfuse = Langfuse()
    dataset_names = []
    for path in sorted(DATASETS_DIR.glob("*.json")):
        definition = load_definition(path.stem)
        sync_dataset(langfuse, definition)
        dataset_names.append(definition["name"])
        print(
            f"Synced dataset '{definition['name']}' ({len(definition['items'])} items)"
        )

    if sync_llm_connection(langfuse):
        ensure_evaluator(langfuse)
        ensure_evaluation_rules(langfuse, dataset_names)

    langfuse.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
