from agent_lab import discoverable_mcp_tool


@discoverable_mcp_tool(
    "{{ cookiecutter.package_name }}_hello_tool",
    description="Returns a friendly greeting. Replace with your own MCP tools.",
    annotations={"readOnlyHint": True},
)
async def hello_tool(container, name: str) -> str:
    return f"Hello, {name}! This is {{ cookiecutter.project_name }}."
