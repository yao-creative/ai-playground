# 06 Agentic Planning

This module rebuilds agentic orchestration as a standalone planning pipeline.

Unlike `05`, which is primarily a ReAct-style tool loop, `06` separates the answer phase into explicit stages:

- planner
- drafter
- reviewer
- redrafter (bounded to one pass in MVP)
- reviewer-gated finalization

The flow keeps grounded retrieval local and deterministic, and returns a safe fallback when review still fails.

## Agentic Planning Request Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant User as User Terminal Input
    participant App as TerminalChatApp<br/>src/06-agentic-planning/terminal_app.py
    participant Orch as AgenticPlanningOrchestrator<br/>src/06-agentic-planning/orchestrator.py
    participant Tools as DocumentTools<br/>src/06-agentic-planning/tools.py
    participant Retriever as BM25RetrievalStrategy or KeywordRetrievalStrategy<br/>src/06-agentic-planning/retrieval.py
    participant OpenAI as OpenAI Responses API

    User->>App: Enter question
    App->>Orch: answer(user_text, chat_history)

    loop bounded evidence collection (max_steps)
        Orch->>OpenAI: responses.create(input=evidence_prompt)
        OpenAI-->>Orch: Action:{...} or Stop:{...}
        alt Action search/read
            Orch->>Tools: validate_action + execute
            alt search_documents
                Tools->>Retriever: retrieve(query, documents, limit)
                Retriever-->>Tools: ranked documents
            end
            Tools-->>Orch: tool_result payload/error
        else Stop
            Orch->>Orch: exit evidence loop
        end
    end

    Orch->>OpenAI: Planner.run(...)
    OpenAI-->>Orch: PlanResult JSON
    Orch->>OpenAI: Drafter.run(...)
    OpenAI-->>Orch: DraftResult JSON
    Orch->>OpenAI: Reviewer.run(...)
    OpenAI-->>Orch: ReviewResult JSON

    alt review failed and redraft budget > 0
        Orch->>OpenAI: Redrafter.run(...)
        OpenAI-->>Orch: revised DraftResult JSON
        Orch->>OpenAI: Reviewer.run(...) again
        OpenAI-->>Orch: ReviewResult JSON
    end

    alt review pass + supported + citations present
        Orch-->>App: AgentRunResult(supported=true, cited_doc_ids)
    else gate failed or invalid support/citation state
        Orch-->>App: AgentRunResult(supported=false, safe fallback)
    end

    App-->>User: Print final answer (+ Sources when supported)
```

## Agentic Planning Control Flow (Mermaid)

```mermaid
flowchart TD
    A[User Question] --> B[Collect Evidence Loop]
    B --> C{Blocked by policy or invalid action?}
    C -->|Yes| Z[Return safe unsupported fallback]
    C -->|No| D[Build Evidence Summary]

    D --> E[Planner Stage]
    E --> F[Drafter Stage]
    F --> G[Reviewer Stage]

    G --> H{Review passed?}
    H -->|Yes| I[Finalize with support/citation checks]
    H -->|No| J{max_redrafts > 0?}

    J -->|No| Z
    J -->|Yes| K[Redrafter Stage]
    K --> L[Reviewer Stage Again]
    L --> M{Review passed now?}

    M -->|No| Z
    M -->|Yes| I

    I --> N{supported=true and citations exist?}
    N -->|Yes| O[Return supported answer + citations]
    N -->|No| P[Return unsupported answer]
```

## Module Layout

- `main.py`: CLI composition and dependency wiring
- `orchestrator.py`: control plane and stage orchestration
- `stages.py`: planner/drafter/reviewer/redrafter stage implementations
- `tools.py`: retrieval tool boundary (`search_documents`, `read_document`)
- `retrieval.py`: local BM25 + keyword retrieval strategies
- `data.py`: fixed in-memory policy corpus
- `models.py`: typed contracts for stage outputs and final result
- `terminal_app.py`: synchronous terminal UX loop

## Run Notes

Run from repo root:

```bash
make run-agentic-planning
```

Optional flags:

```bash
uv run src/06-agentic-planning/main.py --strategy keyword --max-steps 4 --max-redrafts 1
```

Defaults:

- retrieval strategy: `bm25`
- evidence step budget: `4`
- redraft budget: `1` (MVP hard cap)
