from agent_lab import discoverable_mcp_prompt


@discoverable_mcp_prompt(
    "{{ cookiecutter.package_name }}_greeting_prompt",
    description="A sample system prompt. Replace with your own MCP prompts.",
)
def greeting_prompt(role: str = "assistant") -> str:
    return f"You are a helpful {role} for {{ cookiecutter.project_name }}."
