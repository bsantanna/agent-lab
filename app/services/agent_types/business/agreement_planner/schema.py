from typing_extensions import TypedDict, Literal, Annotated

from app.services.agent_types.business.agreement_planner import SUPERVISED_AGENTS

SUPERVISOR_ROUTER_OPTIONS = SUPERVISED_AGENTS + ["__end__"]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*SUPERVISOR_ROUTER_OPTIONS]


class StructuredReport(TypedDict):
    """Structured report"""


class AgreementPlan(TypedDict):
    """Agreement plan"""


class ClaimSupportRequest(TypedDict):
    """Claim support request"""


class ExpertAnalysis(TypedDict):
    """Expert analysis"""

    agreement_plan: Annotated[
        AgreementPlan,
        ...,
        "An agreement plan to be approved by customer and business partner",
    ]

    claim_support_request: Annotated[
        ClaimSupportRequest, ..., "A claim support request to be analyzed by customer"
    ]
