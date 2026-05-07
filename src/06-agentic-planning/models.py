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
class PlanResult:
    objective: str
    evidence_needed: list[str]
    proposed_actions: list[str]


@dataclass(frozen=True)
class DraftResult:
    answer: str
    cited_doc_ids: list[str]
    supported: bool


@dataclass(frozen=True)
class PlanningSession:
    user_input: str
    chat_history: list[tuple[str, str]]
    steps: list[AgentStep]
    evidence_summary: str
    plan: PlanResult
    revision_count: int = 0
    status: str = "awaiting_user_decision"


@dataclass(frozen=True)
class AgentRunResult:
    final_answer: str
    cited_doc_ids: list[str]
    supported: bool
    steps: list[AgentStep] = field(default_factory=list)
    plan: PlanResult | None = None


@dataclass(frozen=True)
class EvidencePolicyConfig:
    max_search_calls: int = 2
    duplicate_strategy: str = "retry_on_error_only"


@dataclass(frozen=True)
class ActionDecision:
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class StopDecision:
    reason: str = "enough evidence"
