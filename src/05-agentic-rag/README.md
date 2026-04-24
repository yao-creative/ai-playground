# 05 Vanilla Agentic RAG

This module is the smallest step from `03-rag-chat` into agentic RAG. Using ReAct loop.

The earlier `03` flow always retrieves first, then prompts the model with fixed context.
This `05` flow lets the model choose the next action inside a bounded loop:

- search document snippets
- read one full document
- finish with a grounded answer
- finish with an unsupported answer when evidence is weak

The implementation stays local and readable:

- fixed in-memory documents inside this section
- local BM25 or keyword retrieval inside this section
- one synchronous controller loop with streamed step events
- no hosted tools
- no vector store service
- no eval harness inside this lesson

## Agentic RAG Request Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant User as User Terminal Input
    participant App as TerminalChatApp<br/>src/05-agentic-rag/terminal_app.py
    participant Agent as AgenticRAG<br/>src/05-agentic-rag/agent.py
    participant Tools as DocumentTools<br/>src/05-agentic-rag/tools.py
    participant Retriever as BM25RetrievalStrategy or KeywordRetrievalStrategy<br/>src/05-agentic-rag/retrieval.py
    participant OpenAI as OpenAI Responses API

    User->>App: Enter question
    App->>Agent: answer_stream(user_text, chat_history)
    loop bounded by max_steps
        Agent->>Agent: build ReAct prompt with prior observations
        Agent->>OpenAI: responses.create(model, input=prompt, stream=true)
        OpenAI-->>Agent: streamed text deltas
        Agent->>Agent: parse Action/Final envelope
        alt search_documents
            Agent->>Tools: execute(search_documents)
            Tools->>Retriever: retrieve(query, documents, limit)
            Retriever-->>Tools: ranked documents
            Tools-->>Agent: doc ids, titles, categories, snippets
        else read_document
            Agent->>Tools: execute(read_document)
            Tools-->>Agent: full document payload
        else finish
            Agent->>Agent: validate cited_doc_ids and supported flag
            Agent-->>App: AgentRunResult
        end
    end
    App-->>User: Print answer and cited sources
```



## Duplicate Call / Weak Evidence Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Agent as AgenticRAG
    participant OpenAI as OpenAI Responses API
    participant Guard as prior_calls + search_count

    Agent->>OpenAI: request next JSON action
    OpenAI-->>Agent: repeated search_documents call
    Agent->>Guard: normalize tool call
    alt call already seen
        Guard-->>Agent: duplicate
        Agent->>Agent: return unsupported fallback result
    else search count exceeds limit
        Guard-->>Agent: too many searches
        Agent->>Agent: return unsupported fallback result
    else action invalid or unsupported
        Agent->>Agent: coerce to finish with supported=false
    end
```



## Implementation Notes

- `main.py` is self-contained inside `05` and wires only local `data.py`, `retrieval.py`, `agent.py`, and `terminal_app.py`.
- `agent.py` is the control plane. It owns:
  - the bounded step loop
  - ReAct action/final prompt and parsing
  - streamed per-step model deltas
  - duplicate-call prevention
  - search retry limits
  - final answer validation
- `tools.py` is the tool boundary. It only exposes:
  - `search_documents(query, limit)`
  - `read_document(doc_id)`
- `search_documents(...)` returns compact snippets first so the model can decide whether it needs a full document read.
- `Final: {...}` is not a real tool implementation. It is a structured stop signal interpreted inside `agent.py`.
- A supported answer is downgraded to unsupported if it does not include at least one cited document id.
- The chat loop remains synchronous in `terminal_app.py`, and now prints each streamed step output plus action/observation logs.

## Run Notes

Run the lesson from the repo root:

```bash
make run-agentic-rag
```

Optional flags:

```bash
uv run src/05-agentic-rag/main.py --strategy keyword --max-steps 4
```

Defaults:

- retrieval strategy: `bm25`
- step budget: `4`
- answer style: grounded with doc-id citations when supported

