import json
from dataclasses import dataclass, field
from typing import Any

from models import (
    ActionDecision,
    AgentRunResult,
    AgentStep,
    DraftResult,
    EvidencePolicyConfig,
    PlanResult,
    ReviewResult,
    RevisionConfig,
    StopDecision,
    ToolCall,
)
from stages import Drafter, Planner, Redrafter, Reviewer
from tools import DocumentTools


@dataclass
class _EvidencePolicyState:
    search_count: int = 0
    prior_call_counts: dict[str, int] = field(default_factory=dict)
    prior_call_errors: dict[str, bool] = field(default_factory=dict)


class AgenticPlanningOrchestrator:
    EVIDENCE_SYSTEM_PROMPT = """You are an evidence collection controller for grounded QA.
Use tools to collect enough evidence, then stop.
Output exactly one of:
Action: {"tool_name":"search_documents"|"read_document","arguments":{...}}
Stop: {"reason":"string"}
Do not output anything else."""

    SAFE_FALLBACK = "I do not have enough supported evidence to answer confidently."

    def __init__(
        self,
        *,
        client,
        model: str,
        documents,
        retrieval_strategy,
        max_steps: int = 4,
        evidence_policy: EvidencePolicyConfig | None = None,
        revision_config: RevisionConfig | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_steps = max_steps
        self.tools = DocumentTools(documents, retrieval_strategy)
        self.evidence_policy = evidence_policy or EvidencePolicyConfig()
        self.revision_config = revision_config or RevisionConfig()

        self.planner = Planner(client=client, model=model)
        self.drafter = Drafter(client=client, model=model)
        self.reviewer = Reviewer(client=client, model=model)
        self.redrafter = Redrafter(client=client, model=model)

    def answer(self, user_input: str, chat_history: list[tuple[str, str]] | None = None) -> AgentRunResult:
        history = chat_history or []
        steps, blocked = self._collect_evidence(user_input=user_input, chat_history=history)
        if blocked:
            return AgentRunResult(final_answer=self.SAFE_FALLBACK, cited_doc_ids=[], supported=False, steps=steps)

        evidence_summary = self._build_evidence_summary(steps)
        plan = self.planner.run(
            user_input=user_input,
            chat_history=history,
            evidence_summary=evidence_summary,
        )
        draft = self.drafter.run(
            user_input=user_input,
            plan=plan,
            evidence_summary=evidence_summary,
            chat_history=history,
        )
        review = self.reviewer.run(
            user_input=user_input,
            draft=draft,
            evidence_summary=evidence_summary,
        )

        redrafts = max(0, min(int(self.revision_config.max_redrafts), 1))
        if not review.pass_review and redrafts > 0:
            draft = self.redrafter.run(
                user_input=user_input,
                prior_draft=draft,
                review=review,
                evidence_summary=evidence_summary,
            )
            review = self.reviewer.run(
                user_input=user_input,
                draft=draft,
                evidence_summary=evidence_summary,
            )

        return self._finalize_result(draft=draft, review=review, steps=steps, plan=plan)

    def _collect_evidence(
        self,
        *,
        user_input: str,
        chat_history: list[tuple[str, str]],
    ) -> tuple[list[AgentStep], bool]:
        steps: list[AgentStep] = []
        policy_state = _EvidencePolicyState()

        for step_index in range(1, self.max_steps + 1):
            decision = self._decide_next_action(
                user_input=user_input,
                chat_history=chat_history,
                steps=steps,
                remaining_steps=self.max_steps - step_index + 1,
            )
            if isinstance(decision, StopDecision):
                return steps, False

            try:
                tool_call = self.tools.validate_action(decision.tool_name, decision.arguments)
            except ValueError:
                return steps, True

            if self._should_block_tool_call(tool_call, policy_state):
                return steps, True

            tool_result = self.tools.execute(tool_call)
            steps.append(AgentStep(step_index=step_index, tool_call=tool_call, tool_result=tool_result))
            self._record_call_outcome(tool_call=tool_call, error=tool_result.error, policy_state=policy_state)

        return steps, False

    def _decide_next_action(
        self,
        *,
        user_input: str,
        chat_history: list[tuple[str, str]],
        steps: list[AgentStep],
        remaining_steps: int,
    ) -> ActionDecision | StopDecision:
        prompt = self._build_action_prompt(
            user_input=user_input,
            chat_history=chat_history,
            steps=steps,
            remaining_steps=remaining_steps,
        )
        response = self.client.responses.create(model=self.model, input=prompt, stream=False)
        text = str(getattr(response, "output_text", ""))
        return self._parse_decision(text)

    def _build_action_prompt(
        self,
        *,
        user_input: str,
        chat_history: list[tuple[str, str]],
        steps: list[AgentStep],
        remaining_steps: int,
    ) -> str:
        sections = [
            self.EVIDENCE_SYSTEM_PROMPT,
            "Available tools:",
            *self.tools.list_tool_prompt_schemas(),
            "Rules:",
            "- Use search_documents first for factual questions unless a doc id is directly requested.",
            "- Avoid repeating identical tool calls unless previous call failed.",
            f"Remaining steps: {remaining_steps}",
        ]

        if chat_history:
            sections.append("Conversation history:")
            for speaker, message in chat_history[-6:]:
                sections.append(f"{speaker}: {message}")

        if steps:
            sections.append("Previous tool results:")
            for step in steps:
                sections.append(
                    json.dumps(
                        {
                            "step": step.step_index,
                            "tool_name": step.tool_call.tool_name,
                            "arguments": step.tool_call.arguments,
                            "result": step.tool_result.payload,
                            "error": step.tool_result.error,
                        },
                        ensure_ascii=True,
                    )
                )
        else:
            sections.append("Previous tool results: none")

        sections.append(f"User question: {user_input}")
        return "\n".join(sections)

    def _parse_decision(self, response_text: str) -> ActionDecision | StopDecision:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = [line for line in cleaned.splitlines() if not line.startswith("```")]
            cleaned = "\n".join(lines).strip()

        stop_marker = cleaned.find("Stop:")
        action_marker = cleaned.find("Action:")

        if stop_marker != -1 and (action_marker == -1 or stop_marker < action_marker):
            payload = self._extract_json_object(cleaned[stop_marker + len("Stop:") :])
            reason = "enough evidence"
            if isinstance(payload, dict):
                reason = str(payload.get("reason", reason)).strip() or reason
            return StopDecision(reason=reason)

        payload = self._extract_json_object(cleaned[action_marker + len("Action:") :] if action_marker != -1 else cleaned)
        if not isinstance(payload, dict):
            return StopDecision(reason="invalid action output")

        tool_name = str(payload.get("tool_name", "")).strip()
        arguments = payload.get("arguments", {})
        if not tool_name or not isinstance(arguments, dict):
            return StopDecision(reason="invalid action payload")

        return ActionDecision(tool_name=tool_name, arguments=arguments)

    def _extract_json_object(self, response_text: str) -> dict[str, Any] | None:
        cleaned = response_text.strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                parsed = json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None
        return parsed if isinstance(parsed, dict) else None

    def _normalize_tool_call(self, tool_call: ToolCall) -> str:
        return json.dumps(
            {
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
            },
            sort_keys=True,
            ensure_ascii=True,
        )

    def _should_block_tool_call(self, tool_call: ToolCall, policy_state: _EvidencePolicyState) -> bool:
        normalized_call = self._normalize_tool_call(tool_call)
        prior_count = policy_state.prior_call_counts.get(normalized_call, 0)
        if prior_count > 0 and self.evidence_policy.duplicate_strategy == "retry_on_error_only":
            previous_error = policy_state.prior_call_errors.get(normalized_call, False)
            if not previous_error:
                return True
        if prior_count > 0 and self.evidence_policy.duplicate_strategy == "always_block":
            return True

        if tool_call.tool_name == "search_documents":
            projected_count = policy_state.search_count + 1
            if projected_count > self.evidence_policy.max_search_calls:
                return True
            policy_state.search_count = projected_count

        return False

    def _record_call_outcome(
        self,
        *,
        tool_call: ToolCall,
        error: str | None,
        policy_state: _EvidencePolicyState,
    ) -> None:
        normalized_call = self._normalize_tool_call(tool_call)
        policy_state.prior_call_counts[normalized_call] = policy_state.prior_call_counts.get(normalized_call, 0) + 1
        policy_state.prior_call_errors[normalized_call] = bool(error)

    def _build_evidence_summary(self, steps: list[AgentStep]) -> str:
        if not steps:
            return "No tool evidence collected."

        rows = []
        for step in steps:
            rows.append(
                json.dumps(
                    {
                        "step": step.step_index,
                        "tool": step.tool_call.tool_name,
                        "arguments": step.tool_call.arguments,
                        "payload": step.tool_result.payload,
                        "error": step.tool_result.error,
                    },
                    ensure_ascii=True,
                )
            )
        return "\n".join(rows)

    def _finalize_result(
        self,
        *,
        draft: DraftResult,
        review: ReviewResult,
        steps: list[AgentStep],
        plan: PlanResult,
    ) -> AgentRunResult:
        cited_doc_ids = [str(doc_id) for doc_id in draft.cited_doc_ids]
        supported = bool(draft.supported and review.pass_review and cited_doc_ids)

        if not review.pass_review:
            return AgentRunResult(
                final_answer=self.SAFE_FALLBACK,
                cited_doc_ids=[],
                supported=False,
                steps=steps,
                plan=plan,
                review=review,
            )

        answer = draft.answer.strip() or self.SAFE_FALLBACK
        if draft.supported and not cited_doc_ids:
            supported = False

        if supported:
            return AgentRunResult(
                final_answer=answer,
                cited_doc_ids=cited_doc_ids,
                supported=True,
                steps=steps,
                plan=plan,
                review=review,
            )

        return AgentRunResult(
            final_answer=answer,
            cited_doc_ids=[],
            supported=False,
            steps=steps,
            plan=plan,
            review=review,
        )
