import os

from scenario.config import ModelConfig

JUDGE_MODEL = os.getenv("SIMULATION_JUDGE_MODEL", "openai/gpt-5-nano")
JUDGE_API_BASE = os.getenv("SIMULATION_JUDGE_API_BASE")
JUDGE_API_KEY = os.getenv("SIMULATION_JUDGE_API_KEY")


def judge_model_config() -> ModelConfig:
    return ModelConfig(
        model=JUDGE_MODEL,
        api_base=JUDGE_API_BASE,
        api_key=JUDGE_API_KEY,
    )
