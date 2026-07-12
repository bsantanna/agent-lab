import langwatch
from langwatch.generated.langwatch_rest_api_client.api.default import (
    get_api_dataset_by_slug_or_id,
)
from langwatch.generated.langwatch_rest_api_client.models import (
    GetApiDatasetBySlugOrIdResponse200,
)
from langwatch.state import get_instance

from tests.simulation.common.datasets import load_definition
from tests.simulation.common.judge import evaluate

# all definitions share one LangWatch dataset: the free plan allows only
# 3 datasets per project, so items carry a "dataset" column instead
CONSOLIDATED_DATASET_NAME = "simulations"

# entries are schema-validated server-side against the dataset's columnTypes
DATASET_COLUMNS = [
    {"name": "item_id", "type": "string"},
    {"name": "dataset", "type": "string"},
    {"name": "input", "type": "string"},
    {"name": "expected_output", "type": "string"},
    {"name": "agent_type", "type": "string"},
]


def _ensure_dataset(client) -> str:
    """Return the consolidated dataset slug, creating the dataset if missing.

    The create/list endpoints are not wrapped by the SDK's generated client,
    so they are called through its authenticated httpx client. The server
    slugifies the dataset name (underscores become dashes), so the returned
    slug must be used for all follow-up calls.
    """
    http = client.get_httpx_client()
    listing = http.get("/api/dataset", params={"limit": 200})
    listing.raise_for_status()
    for dataset in listing.json()["data"]:
        if dataset["name"] == CONSOLIDATED_DATASET_NAME:
            return dataset["slug"]

    response = http.post(
        "/api/dataset",
        json={"name": CONSOLIDATED_DATASET_NAME, "columnTypes": DATASET_COLUMNS},
    )
    response.raise_for_status()
    return response.json()["slug"]


def sync_dataset_entries(definition: dict) -> str:
    """Create the consolidated LangWatch dataset if needed and append the
    definition's missing items, matched by the item_id column. Idempotent:
    already-synced items are skipped. Returns the dataset slug."""
    langwatch.ensure_setup()
    client = get_instance().rest_api_client
    slug = _ensure_dataset(client)
    dataset = get_api_dataset_by_slug_or_id.sync(slug_or_id=slug, client=client)
    if not isinstance(dataset, GetApiDatasetBySlugOrIdResponse200):
        raise RuntimeError(
            f"LangWatch dataset '{CONSOLIDATED_DATASET_NAME}' is not accessible: "
            f"{getattr(dataset, 'message', dataset)}"
        )

    existing_ids = {item.entry.to_dict().get("item_id") for item in dataset.data}
    entries = [
        {
            "item_id": item["id"],
            "dataset": definition["name"],
            "input": item["input"]["message"],
            "expected_output": "\n".join(item["expected_output"]["criteria"]),
            "agent_type": item.get("metadata", {}).get("agent_type", ""),
        }
        for item in definition["items"]
        if item["id"] not in existing_ids
    ]
    if entries:
        response = client.get_httpx_client().post(
            f"/api/dataset/{slug}/entries", json={"entries": entries}
        )
        response.raise_for_status()
    return slug


def run_simulation(client, dataset_key: str, agent_fn) -> list:
    definition = load_definition(dataset_key)
    sync_dataset_entries(definition)

    experiment = langwatch.experiment.init(f"{definition['name']}_experiment")
    results = []
    for index, item in enumerate(experiment.loop(definition["items"], threads=1)):
        message = item["input"]["message"]
        output = agent_fn(client, message)
        verdict = evaluate(message, output, item["expected_output"]["criteria"])
        experiment.log(
            "llm_as_judge",
            index=index,
            data={"input": message, "output": output},
            score=verdict["score"],
            passed=verdict["passed"],
            details=verdict["reasoning"],
        )
        results.append(
            {
                "item_id": item["id"],
                "passed": verdict["passed"],
                "score": verdict["score"],
                "reasoning": verdict["reasoning"],
                "output": output,
            }
        )
    return results
