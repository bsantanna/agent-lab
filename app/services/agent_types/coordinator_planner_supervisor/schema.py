from typing_extensions import TypedDict, Literal, Annotated

from app.services.agent_types.coordinator_planner_supervisor import SUPERVISED_AGENTS

SUPERVISOR_ROUTER_OPTIONS = SUPERVISED_AGENTS + ["__end__"]


class CoordinatorRouter(TypedDict):
    """Decide to route to next step between planner and __end__"""

    next: Literal["planner", "__end__"]
    generated: Annotated[
        str, ..., "Empty if next is planner, a generated answer if next is __end__"
    ]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*SUPERVISOR_ROUTER_OPTIONS]
