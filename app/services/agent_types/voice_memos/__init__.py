SUPERVISED_AGENT_CONFIGURATION = {
    "content_analyst": {
        "name": "content_analyst",
        "desc": (
            "Responsible for mapping relevant information, understanding user needs and conducting content analysis"
        ),
        "desc_for_llm": ("Outputs a Markdown report with findings."),
        "is_optional": False,
    },
    "reporter": {
        "name": "reporter",
        "desc": ("Responsible for formatting answer to the user as a JSON document"),
        "desc_for_llm": "Format answer to the user as a JSON document",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())

AZURE_CONTENT_ANALYST_TOOLS_CONFIGURATION = {
    "person_search": {
        "name": "person_search",
        "desc": (
            "Use this tool to search for individuals within the domain or organization. "
            "It is particularly useful for looking up co-workers' profiles, such as their roles, departments, or contact information. "
            "For example, you can search for 'John Doe' to retrieve relevant details about their position and team."
        ),
    },
    "person_details": {
        "name": "person_details",
        "desc": (
            "Use this tool to retrieve detailed information about a person using their email address as a parameter. "
            "For instance, providing 'jane.doe@example.com' will return details such as their full name, job title, and organizational affiliation."
        ),
    },
}

AZURE_CONTENT_ANALYST_TOOLS = list(AZURE_CONTENT_ANALYST_TOOLS_CONFIGURATION.keys())
