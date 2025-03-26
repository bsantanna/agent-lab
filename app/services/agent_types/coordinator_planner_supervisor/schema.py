from langgraph.constants import END
from typing_extensions import TypedDict, Literal, Annotated

from app.services.agent_types.coordinator_planner_supervisor import SUPERVISED_AGENTS


class CoordinatorRouter(TypedDict):
    """Decide to route to next step between PLANNER and FINISH"""

    next: Literal["planner", END]
    generated: Annotated[str, ..., "Generated answer to the query"]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[SUPERVISED_AGENTS + [END]]
