from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from typing import Annotated, List, TypedDict


class AgentState(TypedDict):
    query: str
    generation: str
    documents: List[str]
    messages: Annotated[List[AnyMessage], add_messages]
    subject_filter_prompt: str
    execution_system_prompt: str
