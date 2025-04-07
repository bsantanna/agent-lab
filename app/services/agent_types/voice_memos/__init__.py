SUPERVISED_AGENT_CONFIGURATION ={
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
