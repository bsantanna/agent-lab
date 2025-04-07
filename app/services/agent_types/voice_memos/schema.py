from typing_extensions import TypedDict, Literal, Annotated

from app.services.agent_types.voice_memos import SUPERVISED_AGENTS

SUPERVISOR_ROUTER_OPTIONS = SUPERVISED_AGENTS + ["__end__"]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*SUPERVISOR_ROUTER_OPTIONS]


class VoiceCoordinatorRouter(TypedDict):
    """Transcribe the audio and decide to route to next step between planner and __end__"""

    next: Literal["planner", "__end__"]
    transcription: Annotated[
        str, ..., "Audio transcription of the voice memo"
    ]
