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

COORDINATOR_TOOLS_CONFIGURATION = {
    "tavily_search": {
        "name": "tavily_search",
        "desc": (
            "A search engine optimized for comprehensive, accurate, and trusted results. "
            "Useful for when you need to answer questions about current events. "
            "It not only retrieves URLs and snippets, but offers advanced search depths, "
            "domain management, time range filters, and image search, this tool delivers "
            "real-time, accurate, and citation-backed results."
            "Input should be a search query."
        ),
    },
    "tavily_extract": {
        "name": "tavily_extract",
        "desc": (
            "Extracts comprehensive content from web pages based on provided URLs. "
            "This tool retrieves raw text of a web page, with an option to include images. "
            "It supports two extraction depths: 'basic' for standard text extraction and "
            "'advanced' for a more comprehensive extraction with higher success rate. "
            "Ideal for use cases such as content curation, data ingestion for NLP models, "
            "and automated information retrieval, this endpoint seamlessly integrates into "
            "your content processing pipeline. Input should be a list of one or more URLs."
        ),
    },
}

COORDINATOR_TOOLS = list(COORDINATOR_TOOLS_CONFIGURATION.keys())

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
