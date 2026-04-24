from dataclasses import dataclass, field
from typing import Any, Literal


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
class AgentEvent:
    event_type: Literal[
        "step_started",
        "model_delta",
        "action_selected",
        "observation",
        "step_error",
        "final_result",
    ]
    step_index: int | None = None
    delta: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None
    message: str | None = None
    run_result: AgentRunResult | None = None
