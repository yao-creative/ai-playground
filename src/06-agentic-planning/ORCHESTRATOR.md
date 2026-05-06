# Orchestrator Function Reference

This document explains the functions in `orchestrator.py`, what each does, and why it exists.

## File

- `src/06-agentic-planning/orchestrator.py`

## Data Structure

### `_EvidencePolicyState`
- What: Internal mutable state for evidence-loop policy checks.
- Fields:
  - `search_count`: number of `search_documents` calls used so far.
  - `prior_call_counts`: normalized tool-call -> execution count.
  - `prior_call_errors`: normalized tool-call -> whether previous attempt errored.
- Why: Keeps duplicate-call and search-budget enforcement separate from stage logic.

## Class

### `AgenticPlanningOrchestrator`
- What: Control plane for one user turn.
- Why: Centralizes deterministic workflow ordering and safety gates.

### `__init__(...)`
- What: Wires model client, retrieval tools, policy config, revision config, and stage objects (`Planner`, `Drafter`, `Reviewer`, `Redrafter`).
- Why: Dependency injection keeps orchestration testable and easy to swap components.

### `answer(user_input, chat_history=None) -> AgentRunResult`
- What: Main entrypoint for one turn.
- Steps:
  1. Collect evidence with bounded tool loop.
  2. Build evidence summary.
  3. Run planner, drafter, reviewer.
  4. Optionally run one redraft + second review.
  5. Finalize output with gating rules.
- Why: Enforces `plan -> draft -> review -> redraft -> review -> finalize` in one explicit pipeline.

### `_collect_evidence(...) -> tuple[list[AgentStep], bool]`
- What: Executes bounded Action/Stop loop to gather evidence before drafting.
- Returns:
  - `steps`: tool execution trace.
  - `blocked`: whether loop stopped for policy/validation failure.
- Why: Isolates tool-use phase from writing/review phases and allows early safe fallback.

### `_decide_next_action(...) -> ActionDecision | StopDecision`
- What: Sends evidence-loop prompt to model and parses result.
- Why: Keeps model call/parsing for evidence actions in one place.

### `_build_action_prompt(...) -> str`
- What: Builds prompt for evidence controller with tools, rules, history, prior tool results, and remaining budget.
- Why: Makes loop behavior explicit and reproducible.

### `_parse_decision(response_text) -> ActionDecision | StopDecision`
- What: Parses model output for `Action: {...}` or `Stop: {...}` envelopes.
- Why: Converts free text into strict control-plane decisions.

### `_extract_json_object(response_text) -> dict | None`
- What: Extracts JSON object from possibly noisy model text.
- Why: Defensive parsing to reduce hard failures from minor formatting drift.

### `_normalize_tool_call(tool_call) -> str`
- What: Canonical JSON string for tool name + args.
- Why: Stable key for duplicate detection and prior-call bookkeeping.

### `_should_block_tool_call(tool_call, policy_state) -> bool`
- What: Applies evidence policy:
  - duplicate handling strategy
  - max search calls
- Why: Prevents low-value loops and controls tool budget.

### `_record_call_outcome(tool_call, error, policy_state) -> None`
- What: Updates call counts and error history after each tool execution.
- Why: Feeds duplicate strategy (`retry_on_error_only`, etc.).

### `_build_evidence_summary(steps) -> str`
- What: Serializes tool trace into compact JSON lines.
- Why: Provides planner/drafter/reviewer/redrafter with the same grounded evidence snapshot.

### `_finalize_result(draft, review, steps, plan) -> AgentRunResult`
- What: Final gate for output correctness.
- Rules:
  - If review fails: return safe unsupported fallback.
  - Supported answers require citations.
  - Preserve plan/review/step trace in result.
- Why: Guarantees safety invariants even if generation stages produce optimistic output.

## Safety Invariants Enforced Here

- Failed reviewer gate => unsupported fallback.
- `supported=true` is valid only when citations exist.
- Evidence-loop policy can stop low-signal or invalid tool execution.
