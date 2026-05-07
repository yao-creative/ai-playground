# Orchestrator Function Reference

## File

- `src/06-agentic-planning/orchestrator.py`

## Core Structures

### `_EvidencePolicyState`
- Tracks search-call count, normalized call counts, and whether prior calls errored.
- Exists to keep evidence-loop policy state separate from plan generation state.

### `PlanningSession`
- Carries the user question, inherited chat history, evidence steps, evidence summary, current plan, and revision count.
- Exists so the terminal app can keep a stable plan loop without recollecting evidence on every redraft.

## `AgenticPlanningOrchestrator`

### `prepare_plan(user_input, chat_history=None) -> PlanningSession | AgentRunResult`
- Collects evidence first.
- Returns a safe fallback result if evidence collection is blocked.
- Otherwise builds the initial `PlanResult` and packages it into a `PlanningSession`.

### `redraft_plan(session, user_feedback) -> PlanningSession`
- Rewrites the current plan using the same evidence snapshot plus the user feedback.
- Increments `revision_count`.
- Does not rerun retrieval.

### `execute_accepted_plan(session) -> AgentRunResult`
- Drafts the final answer from the accepted plan and existing evidence.
- Finalizes support status from the draft output and citation state.

## Evidence Helpers

### `_collect_evidence(...)`
- Runs the bounded `Action` / `Stop` loop.
- Returns `(steps, blocked)` so the caller can short-circuit safely.

### `_build_action_prompt(...)`
- Serializes tool schemas, policy rules, recent chat history, and prior tool results into the evidence-controller prompt.

### `_parse_decision(...)`
- Converts noisy model output into either `ActionDecision` or `StopDecision`.

### `_should_block_tool_call(...)`
- Applies duplicate-call policy and search-budget limits.

### `_build_evidence_summary(...)`
- Converts collected steps into compact JSON lines shared by planner, plan redrafter, and drafter.

### `_finalize_result(...)`
- Ensures `supported=True` only when citations are present.
- Returns unsupported output otherwise.

## Safety Invariants

- Evidence-loop policy can stop invalid or low-value tool use.
- Plan redrafts reuse evidence; they do not silently recollect it.
- Supported answers require citations.
