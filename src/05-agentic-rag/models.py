from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    payload: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True)
class AgentStep:
    step_index: int
    tool_call: ToolCall
    tool_result: ToolResult


@dataclass(frozen=True)
class AgentRunResult:
    final_answer: str
    cited_doc_ids: list[str]
    supported: bool
    steps: list[AgentStep] = field(default_factory=list)


@dataclass(frozen=True)
class ActionDecision:
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class FinalDecision:
    answer: str
    cited_doc_ids: list[str]
    supported: bool


Decision: TypeAlias = ActionDecision | FinalDecision


@dataclass(frozen=True)
class AgentPolicyConfig:
    max_search_calls: int = 2
    duplicate_strategy: Literal["always_block", "retry_on_error_only", "allow_one_duplicate"] = (
        "retry_on_error_only"
    )


@dataclass(frozen=True)
class StepStartedEvent:
    step_index: int
    event_type: Literal["step_started"] = "step_started"


@dataclass(frozen=True)
class ModelDeltaEvent:
    step_index: int
    delta: str
    event_type: Literal["model_delta"] = "model_delta"


@dataclass(frozen=True)
class ActionSelectedEvent:
    step_index: int
    tool_call: ToolCall
    event_type: Literal["action_selected"] = "action_selected"


@dataclass(frozen=True)
class ObservationEvent:
    step_index: int
    tool_result: ToolResult
    event_type: Literal["observation"] = "observation"


@dataclass(frozen=True)
class StepErrorEvent:
    step_index: int
    message: str
    event_type: Literal["step_error"] = "step_error"


@dataclass(frozen=True)
class FinalResultEvent:
    run_result: AgentRunResult
    event_type: Literal["final_result"] = "final_result"


AgentEvent: TypeAlias = (
    StepStartedEvent
    | ModelDeltaEvent
    | ActionSelectedEvent
    | ObservationEvent
    | StepErrorEvent
    | FinalResultEvent
)
