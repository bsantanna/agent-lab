from typing_extensions import TypedDict, Literal, Annotated

from app.services.agent_types.business.voice_memos import SUPERVISED_AGENTS

SUPERVISOR_ROUTER_OPTIONS = SUPERVISED_AGENTS + ["__end__"]


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*SUPERVISOR_ROUTER_OPTIONS]


class AudioAnalysisReport(TypedDict):
    main_topic: Annotated[str, ..., "The main subject of the transcription."]
    discussed_points: Annotated[
        str, ..., "List of points discussed in the transcription."
    ]
    decisions_taken: Annotated[
        str, ..., "List of decisions made during the transcription."
    ]
    next_steps: Annotated[str, ..., "Follow-ups."]
    action_points: Annotated[str, ..., "Tasks assigned and responsibilities."]
    named_entities: Annotated[
        str, ..., "List names of people and their corresponding organizations."
    ]
