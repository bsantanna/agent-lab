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
            "Responsible for formatting answer to the user as a JSON document"
        ),
        "desc_for_llm": "Format answer to the user as a JSON document",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())
