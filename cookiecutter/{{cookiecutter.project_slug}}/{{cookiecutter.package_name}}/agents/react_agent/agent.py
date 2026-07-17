from datetime import datetime
from pathlib import Path

from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent

from agent_lab import AgentUtils, WorkflowAgentBase, discoverable_agent
from agent_lab.interface.api.messages.schema import MessageRequest


class ReactAgentState(MessagesState):
    agent_id: str
    schema: str
    query: str
    generation: str


@discoverable_agent("{{ cookiecutter.package_name }}_react")
class ReactAgent(WorkflowAgentBase):
    """Single-node ReAct workflow.

    The node runs a ReAct agent over the query and the persisted
    chain-of-thought history; ``messages`` in the checkpointed state stores
    one thought chain per turn (via ``create_thought_chain``), so past turns
    feed the next invocation as conversation memory.
    """

    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def create_default_settings(self, agent_id: str, schema: str):
        current_dir = Path(__file__).parent
        prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=prompt,
            schema=schema,
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(ReactAgentState)
        workflow_builder.add_node("react", self.react)
        workflow_builder.add_edge(START, "react")
        workflow_builder.add_edge("react", END)
        return workflow_builder

    def react(self, state: ReactAgentState):
        agent_id = state["agent_id"]
        schema = state["schema"]
        query = state["query"]

        settings = self.agent_setting_service.get_agent_settings(agent_id, schema)
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }
        execution_system_prompt = self.parse_prompt_template(
            settings_dict,
            "execution_system_prompt",
            {"CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")},
        )

        # No inner checkpointer: the outer WorkflowAgentBase graph owns
        # persistence for this thread. Prior thought chains in state
        # ``messages`` provide the conversation memory.
        react_agent = create_react_agent(
            model=self.get_chat_model(agent_id, schema),
            tools=[],
            prompt=execution_system_prompt,
        )
        response = react_agent.invoke(
            {
                "messages": [
                    *state["messages"],
                    ("human", self.QUERY_FORMAT.format(query=query)),
                ]
            }
        )
        generation = response["messages"][-1].content

        return {
            "generation": generation,
            "messages": [
                self.create_thought_chain(human_input=query, ai_response=generation)
            ],
        }

    def get_input_params(self, message_request: MessageRequest, schema: str) -> dict:
        return {
            "agent_id": message_request.agent_id,
            "schema": schema,
            "query": message_request.message_content,
        }

    def format_response(self, workflow_state: ReactAgentState) -> (str, dict):
        return workflow_state.get("generation"), {
            "agent_id": workflow_state.get("agent_id"),
            "query": workflow_state.get("query"),
            "generation": workflow_state.get("generation"),
            "thought_chain": [
                message.content for message in workflow_state.get("messages", [])
            ],
        }
