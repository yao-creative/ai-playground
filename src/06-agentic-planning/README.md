# 06 Agentic Planning

This module now uses a user-visible planning loop instead of an internal reviewer/redrafter answer loop.

Flow per turn:

1. Collect evidence with the bounded tool loop.
2. Draft a plan spec from that evidence.
3. Show the plan spec to the user.
4. Stay in the plan loop until the user:
   - chooses `accept`
   - chooses `redraft`, then gives feedback
   - exits the plan loop
5. If accepted, execute the accepted plan immediately and print the grounded answer.

## Request Sequence

```mermaid
sequenceDiagram
    autonumber
    participant User as User Terminal Input
    participant App as TerminalChatApp
    participant Orch as AgenticPlanningOrchestrator
    participant Tools as DocumentTools
    participant Retriever as Retrieval Strategy
    participant OpenAI as OpenAI Responses API

    User->>App: Ask question
    App->>Orch: prepare_plan(user_text, chat_history)

    loop bounded evidence collection
        Orch->>OpenAI: responses.create(input=evidence_prompt)
        OpenAI-->>Orch: Action:{...} or Stop:{...}
        alt Action
            Orch->>Tools: validate_action + execute
            Tools->>Retriever: retrieve/read
            Retriever-->>Tools: grounded results
            Tools-->>Orch: tool_result
        else Stop
            Orch-->>Orch: finish evidence loop
        end
    end

    Orch->>OpenAI: Planner.run(...)
    OpenAI-->>Orch: PlanResult JSON
    Orch-->>App: PlanningSession
    App-->>User: Print plan spec

    loop until user decides
        alt user chooses redraft
            App-->>User: ask for redraft feedback
            User->>App: send feedback
            App->>Orch: redraft_plan(session, feedback)
            Orch->>OpenAI: PlanRedrafter.run(...)
            OpenAI-->>Orch: revised PlanResult JSON
            Orch-->>App: revised PlanningSession
            App-->>User: Print revised plan spec
        else user accepts
            App->>Orch: execute_accepted_plan(session)
            Orch->>OpenAI: Drafter.run(...)
            OpenAI-->>Orch: DraftResult JSON
            Orch-->>App: AgentRunResult
            App-->>User: Print final answer (+ sources when supported)
        else user exits
            App-->>User: Abort current turn without drafting answer
        end
    end
```

## Module Layout

- `main.py`: CLI wiring
- `orchestrator.py`: evidence collection plus `prepare_plan`, `redraft_plan`, `execute_accepted_plan`
- `stages.py`: planner, user-feedback plan redrafter, and final drafter
- `tools.py`: retrieval tool boundary
- `models.py`: planning session, plan, and final answer contracts
- `terminal_app.py`: explicit terminal-managed plan loop

## Notes

- Evidence is collected once per planning session and reused across plan redrafts.
- After a plan is shown, the terminal app requires an explicit `accept`, `redraft`, or `exit plan` choice before it interprets free-form text.
- Supported answers still require citations.
- `--max-redrafts` has been removed; the user controls the loop explicitly.
