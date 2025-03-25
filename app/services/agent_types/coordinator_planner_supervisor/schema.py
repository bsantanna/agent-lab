from typing_extensions import TypedDict, Literal

from app.services.agent_types.coordinator_planner_supervisor import SUPERVISED_AGENTS

OPTIONS = SUPERVISED_AGENTS + ["FINISH"]


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*OPTIONS]
