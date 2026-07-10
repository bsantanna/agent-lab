SUPERVISED_AGENT_CONFIGURATION = {
    "content_analyst": {
        "name": "content_analyst",
        "desc": (
            "Responsible for mapping relevant information, understanding user needs and conducting content analysis"
        ),
        "desc_for_llm": "Outputs a Markdown report with findings.",
        "is_optional": False,
    },
    "reporter": {
        "name": "reporter",
        "desc": "Responsible for formatting answer to the user as a JSON document",
        "desc_for_llm": "Format answer to the user as a JSON document",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())

COORDINATOR_TOOLS_CONFIGURATION = {
    "web_search": {
        "name": "web_search",
        "desc": (
            "A web search engine. "
            "Useful for when you need to answer questions about current events. "
            "It retrieves URLs, titles and content snippets for the given query. "
            "Input should be a search query."
        ),
    },
    "web_crawl": {
        "name": "web_crawl",
        "desc": (
            "Extracts content from web pages based on provided URLs and returns it as markdown. "
            "Ideal for reading the full content of pages found via web_search. "
            "Input should be a list of one or more URLs."
        ),
    },
}

COORDINATOR_TOOLS = list(COORDINATOR_TOOLS_CONFIGURATION.keys())

AZURE_COORDINATOR_TOOLS_CONFIGURATION = {
    **COORDINATOR_TOOLS_CONFIGURATION,
    "ical_attachment": (
        "Creates an iCalendar attachment and returns a link to download it."
        "Use this tool to create appointments or other types of events per user request."
        "This tool generates an attachment with corresponding URL, you must forward it to "
        "the user so they can download it."
    ),
}

AZURE_COORDINATOR_TOOLS = list(AZURE_COORDINATOR_TOOLS_CONFIGURATION.keys())

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
