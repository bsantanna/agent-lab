SUPERVISED_AGENT_CONFIGURATION ={
    "content_analyst": {
        "name": "content_analyst",
        "desc": (
            "Responsible for mapping relevant information, understanding user needs and conducting content analysis"
        ),
        "desc_for_llm": (
            "Outputs a Markdown report with findings."
        ),
        "is_optional": False,
    },
    "reporter": {
        "name": "reporter",
        "desc": (
            "Responsible for summarizing analysis results, generating an structured, clear, concise and well formatted voice memo outcome to users"
        ),
        "desc_for_llm": "Write a professional voice memo note based on the result of each step.",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())
