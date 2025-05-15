from typing_extensions import TypedDict, Literal, Annotated, List

from app.services.agent_types.business.agreement_planner import SUPERVISED_AGENTS

SUPERVISOR_ROUTER_OPTIONS = SUPERVISED_AGENTS + ["__end__"]


class CoordinatorRouter(TypedDict):
    """
    Based on provided context, decided te route to take next.
    """

    next: Annotated[
        Literal["planner", "__end__"],
        ...,
        "If customer has supplied enough information, route to planner, otherwise route to __end__",
    ]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*SUPERVISOR_ROUTER_OPTIONS]


class StructuredReport(TypedDict):
    """Structured report"""

    executive_summary: Annotated[str, ..., "An executive summary of the report"]

    key_findings: Annotated[str, ..., "Key findings of the report"]

    detailed_analysis: Annotated[str, ..., "Detailed analysis of the report"]

    conclusions_recommendations: Annotated[
        str, ..., "Conclusions and recommendations of the report"
    ]


class AgreementPlan(TypedDict):
    """Agreement plan"""

    created_by: Annotated[str, ..., "The agent who created the plan"]

    title: Annotated[str, ..., "Title of the agreement plan"]

    description: Annotated[
        str, ..., "Description of the agreement plan containing a professional report"
    ]

    agreement_type: Annotated[
        Literal["financial_agreement_plan", "customer_loss_agreement_plan"],
        ...,
        "Type of agreement plan",
    ]


class CustomerLossAgreementPlan(AgreementPlan):
    """Customer loss agreement plan"""

    damage_report: Annotated[
        str, ..., "Analysis of damage containing a professional report"
    ]

    compensation_report: Annotated[
        str, ..., "Analysis of compensation containing a professional report"
    ]


class FinancialAgreementPlan(AgreementPlan):
    """Financial agreement plan"""

    debt_exposure_category: Annotated[
        Literal["low_financial_risk", "medium_financial_risk", "high_financial_risk"],
        ...,
        "Category of debt exposure",
    ]

    debt_exposure_report: Annotated[
        str, ..., "Analysis of debt exposure containing a professional report"
    ]


class AgreementImpediment(TypedDict):
    """An impediment to reach an agreement"""

    created_by: Annotated[str, ..., "The agent who created the impediment"]

    supporting_evidence: Annotated[
        str,
        ...,
        "An argument requesting supporting evidence or clarification from the customer that could support the removal of the impediment",
    ]

    examples: Annotated[
        List[str],
        ...,
        "Examples of documents that supplies evidence that supports the removal of the impediment that customer should provide",
    ]


class ImpedimentAnalysis(TypedDict):
    """Impediment analysis, containing outcome out analysis and next step"""

    next: Annotated[
        Literal["planner", "__end__"],
        ...,
        "'planner' if analyzed evidence supports the removal of impediment, '__end__' otherwise",
    ]
    analysis: Annotated[
        str,
        ...,
        "Analysis on how the given evidence supports removing the impediment to reach an agreement",
    ]


class FinancialExpertAnalysis(TypedDict):
    """A financial expert analysis containing either an agreement plan in case an agreement can be reached
    or a impediment analysis asking for further evidence in case a fact is not substantiated"""

    agreement_plan: Annotated[
        FinancialAgreementPlan,
        ...,
        "An agreement plan to be approved by customer and business partner",
    ]

    agreement_impediment: Annotated[
        AgreementImpediment,
        ...,
        "A impediment request asking further clarifications from customer",
    ]


class CustomerServiceExpertAnalysis(TypedDict):
    """A customer service expert analysis containing either an agreement plan in case an agreement can be reached
    or a impediment analysis asking for further evidence in case a fact is not substantiated"""

    agreement_plan: Annotated[
        CustomerLossAgreementPlan,
        ...,
        "An agreement plan to be approved by customer and business partner",
    ]

    agreement_impediment: Annotated[
        AgreementImpediment,
        ...,
        "An impediment that requires and further clarifications from customer",
    ]
