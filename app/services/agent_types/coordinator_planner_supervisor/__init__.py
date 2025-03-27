SUPERVISED_AGENT_CONFIGURATION = {
    "researcher": {
        "name": "researcher",
        "desc": (
            "Responsible for searching and collecting relevant information, understanding user needs and conducting research analysis"
        ),
        "desc_for_llm": (
            "Uses knowledge bases to gather information from internal databases. "
            "Uses search engines and web crawlers to gather information from the internet. "
            "Outputs a Markdown report summarizing findings. Researcher can not do math or programming."
        ),
        "is_optional": False,
    },
    "coder": {
        "name": "coder",
        "desc": (
            "Responsible for code implementation, debugging and optimization, handling technical programming tasks"
        ),
        "desc_for_llm": (
            "Executes Python or Bash commands, performs mathematical calculations, and outputs a Markdown report. "
            "Must be used for all mathematical computations."
        ),
        "is_optional": True,
    },
    "browser": {
        "name": "browser",
        "desc": "Responsible for web browsing, content extraction and interaction",
        "desc_for_llm": (
            "Directly interacts with web pages, performing complex operations and interactions. "
            "You can also leverage `browser` to perform in-domain search, like Facebook, Instagram, Github, etc."
        ),
        "is_optional": True,
    },
    "reporter": {
        "name": "reporter",
        "desc": (
            "Responsible for summarizing analysis results, generating reports and presenting final outcomes to users"
        ),
        "desc_for_llm": "Write a professional report based on the result of each step.",
        "is_optional": False,
    },
}

SUPERVISED_AGENTS = list(SUPERVISED_AGENT_CONFIGURATION.keys())
