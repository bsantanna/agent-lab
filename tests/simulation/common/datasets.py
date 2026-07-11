import json
from pathlib import Path

DATASETS_DIR = Path(__file__).parent.parent / "datasets"


def load_definition(dataset_key: str) -> dict:
    with open(DATASETS_DIR / f"{dataset_key}.json") as file:
        return json.load(file)
