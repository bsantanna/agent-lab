from langfuse import Langfuse
from langfuse.experiment import Evaluation

from tests.simulation.common.datasets import load_definition
from tests.simulation.common.judge import evaluate


def sync_dataset(langfuse: Langfuse, definition: dict) -> None:
    """Idempotent: datasets are upserted by name and items by id."""
    langfuse.create_dataset(
        name=definition["name"], description=definition.get("description")
    )
    for item in definition["items"]:
        langfuse.create_dataset_item(
            id=item["id"],
            dataset_name=definition["name"],
            input=item["input"],
            expected_output=item["expected_output"],
            metadata=item.get("metadata"),
        )


def llm_judge_evaluator(*, input, output, expected_output, metadata=None, **kwargs):
    verdict = evaluate(input["message"], output, expected_output["criteria"])
    return [
        Evaluation(
            name="llm_as_judge",
            value=verdict["score"],
            comment=verdict["reasoning"],
        ),
        Evaluation(
            name="passed",
            value=verdict["passed"],
            comment=verdict["reasoning"],
            data_type="BOOLEAN",
        ),
    ]


def run_simulation(langfuse: Langfuse, client, dataset_key: str, agent_fn) -> list:
    definition = load_definition(dataset_key)
    sync_dataset(langfuse, definition)
    dataset = langfuse.get_dataset(definition["name"])

    def task(*, item, **kwargs):
        return agent_fn(client, item.input["message"])

    experiment = dataset.run_experiment(
        name=definition["name"],
        description=definition.get("description"),
        task=task,
        evaluators=[llm_judge_evaluator],
        max_concurrency=1,
    )
    langfuse.flush()

    results = []
    processed_item_ids = set()
    for item_result in experiment.item_results:
        processed_item_ids.add(item_result.item.id)
        evaluations = {ev.name: ev for ev in item_result.evaluations}
        judge_eval = evaluations.get("llm_as_judge")
        if judge_eval is None:
            results.append(
                {
                    "item_id": item_result.item.id,
                    "passed": False,
                    "score": 0.0,
                    "reasoning": "LLM judge evaluation is missing (task or evaluator failed).",
                    "output": item_result.output,
                }
            )
            continue
        results.append(
            {
                "item_id": item_result.item.id,
                "passed": bool(evaluations["passed"].value),
                "score": judge_eval.value,
                "reasoning": judge_eval.comment,
                "output": item_result.output,
            }
        )

    # items whose task raised are excluded from item_results; count them as failures
    for item in dataset.items:
        if item.id not in processed_item_ids:
            results.append(
                {
                    "item_id": item.id,
                    "passed": False,
                    "score": 0.0,
                    "reasoning": "Experiment item was not processed (task raised an exception).",
                    "output": None,
                }
            )
    return results
