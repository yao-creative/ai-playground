from dataclasses import dataclass, field
from typing import Any


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
