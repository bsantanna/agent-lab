SUPERVISED_AGENT_CONFIGURATION = {
    "financial_struggle_analyst": {
        "name": "financial_struggle_analyst",
        "expertise": "Financial debt exposure analysis, debt sources, liquidation options and financial advice.",
        "desc": (
            "Responsible for analyzing the customer's financial struggles and providing insights. "
            "It identifies debt sources linked to business partners and profile debt exposure into discrete classes ('low_financial_risk', 'medium_financial_risk', 'high_financial_risk') "
            "Verifies available debt liquidation options via tools. "
            "Advises customer about available liquidation options. "
        ),
        "desc_for_llm": (
            "Write a markdown report with financial exposure analysis, debt sources, liquidation "
            "options and financial advice."
        ),
        "is_optional": True,
    },
    "customer_complaint_analyst": {
        "name": "customer_complaint_analyst",
        "expertise": "Customer complaint claim, accountable business partners, compensation options and customer advice.",
        "desc": (
            "Responsible for analyzing the customer's complaint and providing insights. "
            "Assess damage, financial loss, inconvenience experienced by the customer. "
            "Collects evidence and information to support the claim. "
            "Identifies the related business partner accountability. "
            "Verifies available compensation options via tools. "
            "Advises customer about available compensation options. "
        ),
        "desc_for_llm": (
            "Write a markdown report with customer complaint claim, accountable business partners, "
            "compensation options and customer advice."
        ),
        "is_optional": True,
    },
    "reporter": {
        "name": "reporter",
        "expertise": "",
        "desc": (
            "Responsible for summarizing analysis results, generating reports and presenting final outcomes to users"
        ),
        "desc_for_llm": "Write a professional report based on the result of each step.",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())
