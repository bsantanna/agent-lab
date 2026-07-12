import os

from scenario.config import ModelConfig

JUDGE_MODEL = os.getenv("SIMULATION_JUDGE_MODEL", "openai/gpt-5-nano")
JUDGE_API_BASE = os.getenv("SIMULATION_JUDGE_API_BASE")
JUDGE_API_KEY = os.getenv("SIMULATION_JUDGE_API_KEY")

# Default LLM executing the simulations: an OpenAI API compatible endpoint
# (e.g. a LAN inference server). The judge configuration above stays separate.
SIMULATION_LLM_MODEL = os.getenv("SIMULATION_LLM_MODEL")
SIMULATION_LLM_API_BASE = os.getenv("SIMULATION_LLM_API_BASE")
SIMULATION_LLM_API_KEY = os.getenv("SIMULATION_LLM_API_KEY", "dummy-key")


def judge_model_config() -> ModelConfig:
    return ModelConfig(
        model=JUDGE_MODEL,
        api_base=JUDGE_API_BASE,
        api_key=JUDGE_API_KEY,
    )


def judge_agent_kwargs() -> dict:
    """Explicit params for scenario JudgeAgent: None values fall back to the
    scenario default model (the simulation LLM), mixing judge and LAN endpoints."""
    api_base = JUDGE_API_BASE
    api_key = JUDGE_API_KEY
    if JUDGE_MODEL.startswith("openai/"):
        api_base = api_base or "https://api.openai.com/v1"
        api_key = api_key or os.getenv("OPENAI_API_KEY")
    return {"model": JUDGE_MODEL, "api_base": api_base, "api_key": api_key}


def simulation_model_config() -> ModelConfig:
    return ModelConfig(
        model=f"openai/{SIMULATION_LLM_MODEL}",
        api_base=SIMULATION_LLM_API_BASE,
        api_key=SIMULATION_LLM_API_KEY,
    )
