"""Idempotently provision the simulation datasets in Langfuse.

Reads every dataset definition under tests/simulation/langfuse/datasets and
creates or updates the corresponding Langfuse dataset and items. Safe to
re-run: datasets are upserted by name and items by id.

Usage:
    uv run python scripts/setup_langfuse_evals.py

Requires LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langfuse import Langfuse  # noqa: E402

from tests.simulation.langfuse.runner import (  # noqa: E402
    DATASETS_DIR,
    load_definition,
    sync_dataset,
)


def main() -> int:
    missing = [
        name
        for name in ("LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
        if not os.getenv(name)
    ]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        return 1

    langfuse = Langfuse()
    for path in sorted(DATASETS_DIR.glob("*.json")):
        definition = load_definition(path.stem)
        sync_dataset(langfuse, definition)
        print(
            f"Synced dataset '{definition['name']}' ({len(definition['items'])} items)"
        )
    langfuse.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
