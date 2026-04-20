# Edit 1 Context Engineering Tutorial Plan 2026-04-18 15:23 Branch: no-git

## Context Engineering Learning Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Learner as Learner
    participant Prompting as Prompt Layer
    participant Retrieval as Retrieval Layer
    participant Memory as Memory Layer
    participant Tools as Tooling Layer
    participant Eval as Eval Layer

    Learner->>Prompting: Start with task framing, role, constraints, output schema
    Prompting->>Retrieval: Add only the minimum external facts needed for the task
    Retrieval->>Memory: Persist durable decisions, summaries, and open loops
    Memory->>Tools: Load fresh state through tools instead of overstuffing prompts
    Tools->>Eval: Measure correctness, cost, latency, and failure modes
    Eval->>Learner: Refine context assembly rules and pruning strategy
```

## Tutorial Build Ladder Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant T1 as Tutorial 1<br/>Prompt + Schema
    participant T2 as Tutorial 2<br/>RAG + Context Packing
    participant T3 as Tutorial 3<br/>Session Memory
    participant T4 as Tutorial 4<br/>Tool-Using Agent
    participant T5 as Tutorial 5<br/>Multi-Agent + Eval
    participant Capstone as Capstone<br/>Production Context Router

    T1->>T2: Add retrieved documents and relevance filtering
    T2->>T3: Add trimming, summaries, and state persistence
    T3->>T4: Add tool contracts, MCP boundaries, and retries
    T4->>T5: Add delegation, subagents, and trajectory review
    T5->>Capstone: Add observability, regression evals, and cost controls
```

## Implementation Notes

- Goal: learn context engineering as a systems discipline, not a prompt-writing trick.
- Recommended order: `prompting -> retrieval -> memory -> tools -> orchestration -> evals -> production optimization`.
- Success criterion: by the capstone, the system should reliably decide what to put in context, what to fetch just-in-time, what to summarize, and what to keep outside the context window.

## Core Concepts To Learn

### 1. Context Assembly

- System prompts, task prompts, examples, structured outputs, and guardrails.
- The main skill is selecting the smallest high-signal token set for the next step.
- Learn failure modes: vague prompts, contradictory instructions, stale retrieved context, and oversized tool schemas.

### 2. Retrieval And Context Packing

- Query rewriting, chunking, reranking, top-k selection, citation grounding, and source trust.
- Learn to treat RAG as one input channel, not the whole architecture.
- Practice packing retrieved evidence near the decision point rather than dumping long documents into the window.

### 3. Short-Term Memory

- Conversation state, turn windows, trimming, compaction, and summaries.
- Learn when to keep raw turns, when to compress, and when to restart the working context.
- Practice preserving exact recent turns while summarizing older decisions and open issues.

### 4. Long-Term Memory

- Durable notes, task state, user preferences, working files, and project memory.
- Learn the split between ephemeral working memory and persistent external memory.
- Practice explicit write/read rules so the agent does not pollute memory with low-value observations.

### 5. Tool And Protocol Design

- Function calling, tool contracts, MCP servers, permissions, retries, and tool-result pruning.
- Learn to expose narrow tools with clear decision boundaries.
- Practice just-in-time loading of data via tools rather than front-loading everything into prompts.

### 6. Agent Orchestration

- Single-agent loops, planner/executor splits, reviewer loops, and subagents.
- Learn when multi-agent designs reduce context load versus when they only add coordination overhead.
- Practice returning distilled summaries from workers back to a lead agent.

### 7. Evaluation

- Task-level correctness, citation quality, retrieval recall, tool success rate, latency, and token cost.
- Learn trajectory review: not only whether the final answer was correct, but whether the context path was efficient and robust.
- Practice building regression suites for context failures, not only output failures.

### 8. Production Optimization

- Prompt caching, context-window budgeting, streaming, observability, and safety controls.
- Learn that larger context windows reduce pressure but do not remove the need for pruning and relevance control.
- Practice building cost-aware policies for retrieval, memory reads, and compaction frequency.

## State Of The Art To Internalize (Post-2025)

### A. Context Engineering Replaced Pure Prompt Tuning

- Anthropic's September 29, 2025 engineering post is the clearest recent statement of the shift: context engineering is about curating the full token state available to the model, not only writing prompts.
- The important mental model is finite attention budget. More tokens can degrade recall and focus, so relevance beats volume.

### B. Just-In-Time Context Is Winning Over Naive Preloading

- Current agent guidance has shifted toward keeping lightweight references in memory and loading real data at runtime through tools.
- This enables progressive disclosure: the agent inspects the environment, loads only the useful slices, and keeps the working set small.

### C. Compaction And Memory Are First-Class

- The strongest post-2025 pattern is explicit context management: trim recent turns, summarize old turns, persist notes externally, and clear stale tool output.
- Short-term memory management is now documented as an engineering surface, not an implementation detail.

### D. Bigger Windows Help, But Do Not Remove Context Engineering

- Frontier systems now expose very large windows, but recent guidance still emphasizes compaction, note-taking, and pruning because context quality degrades when the window is stuffed.
- Context awareness and token-budget awareness improve execution, but they do not replace architecture work.

### E. Protocol Standardization Matters

- MCP is becoming a practical interoperability layer for connecting agents to tools, data, and workflows.
- You should treat protocol design as part of context engineering because the protocol determines what can be fetched, when, and at what granularity.

### F. Evals And Observability Are Part Of The Core Stack

- Modern agent stacks now ship with explicit tracing and evaluation paths.
- If you cannot inspect retrieval decisions, tool calls, summaries, and state transitions, you cannot improve the context policy with confidence.

## Core Libraries / Frameworks To Know

### Foundational APIs

- `OpenAI Responses API + Agents SDK`
  - Learn for: stateful conversations, tools, built-in file search/web search, compaction, prompt caching, and agent evaluation loops.
  - Use when: you want a modern first-party stack with strong tool support and direct context-management primitives.

- `Anthropic Claude API + memory/context guidance`
  - Learn for: context engineering mental models, memory patterns, tool design, and long-horizon task techniques.
  - Use when: you want the clearest recent applied guidance on compaction, note-taking, and subagent context isolation.

### Interoperability Layer

- `Model Context Protocol (MCP)`
  - Learn for: standardizing external tools, data sources, and reusable skills.
  - Use when: you want agents to fetch context from heterogeneous systems without custom one-off integrations everywhere.

### Python Orchestration

- `LangGraph`
  - Learn for: durable execution, stateful long-running agents, human-in-the-loop control, and production orchestration.
  - Best tutorial fit: implement planner/executor/reviewer graphs and inspect traces.

- `PydanticAI`
  - Learn for: typed agents, structured IO, dependency injection, and production-grade Python ergonomics.
  - Best tutorial fit: build smaller strongly-typed systems before moving to heavier orchestration.

- `DSPy`
  - Learn for: declarative LM programs, optimization, signatures, and eval-driven prompt/module tuning.
  - Best tutorial fit: learn how to optimize context strategies and modules systematically instead of hand-tweaking prompts.

- `LlamaIndex`
  - Learn for: knowledge-heavy systems, retrieval pipelines, workflows, and agentic RAG.
  - Best tutorial fit: build retrieval-centric assistants where data connectors and workflow composition matter.

### TypeScript Product Layer

- `Vercel AI SDK`
  - Learn for: shipping chat/product interfaces, provider abstraction, tool usage, message persistence, telemetry, and generative UI patterns.
  - Best tutorial fit: frontend or full-stack context-engineering demos where UX and streaming matter.

### Observability / Eval Adjacency

- `LangSmith`
  - Learn for: trace inspection, evaluation, and production debugging of agent workflows.
  - Best tutorial fit: compare alternative context policies on the same task set.

## Tutorials To Do

### Tutorial 1: Prompt Contract And Output Control

- Build a single-call assistant with strong system instructions, explicit constraints, and structured JSON output.
- Learn:
  - instruction hierarchy
  - schema-first outputs
  - example selection
  - refusal and fallback design
- Deliverable:
  - one API route
  - one eval set of 20 inputs
  - one failure log with prompt revisions

### Tutorial 2: Retrieval And Context Packing

- Build a document QA assistant over a small corpus.
- Learn:
  - chunking
  - top-k retrieval
  - reranking
  - citation grounding
  - packing only the evidence needed for the question
- Deliverable:
  - retrieval pipeline
  - citation-aware answer formatter
  - evals for false citations, missed evidence, and irrelevant context

### Tutorial 3: Session Memory And Compaction

- Build a multi-turn assistant that trims old turns, summarizes older state, and persists durable notes.
- Learn:
  - recent-turn retention
  - summary prompts
  - durable session memory
  - replay vs summary tradeoffs
- Deliverable:
  - memory policy document
  - session store
  - tests for memory drift and summary omission

### Tutorial 4: Tool-Using Agent With MCP

- Build an agent that can read local docs, query a simple database, and call at least one external tool through MCP or an equivalent tool interface.
- Learn:
  - tool schema design
  - permissions
  - retries
  - tool-result pruning
  - just-in-time loading
- Deliverable:
  - 3 to 5 tools
  - trace logs
  - failure cases for wrong tool choice and oversized tool outputs

### Tutorial 5: Multi-Agent Research Workflow

- Build a lead agent that delegates retrieval or analysis to focused subagents and receives compressed summaries back.
- Learn:
  - decomposition
  - summary contracts
  - context isolation
  - reviewer loops
  - parallel search vs unnecessary agent sprawl
- Deliverable:
  - planner
  - 2 workers
  - reviewer
  - eval showing when multi-agent improves quality or speed

### Tutorial 6: Capstone Production Context Router

- Build an app that decides per request which context sources to load: prompt template, memory, retrieval, tool output, or human escalation.
- Learn:
  - policy routing
  - token budgeting
  - caching
  - tracing
  - cost/latency tradeoffs
- Deliverable:
  - routing policy
  - live traces
  - regression suite
  - dashboard for quality, cost, and latency

## Suggested Learning Order

### Week 1

- Learn prompt contracts and structured outputs.
- Finish Tutorial 1.

### Week 2

- Learn retrieval, ranking, and evidence packing.
- Finish Tutorial 2.

### Week 3

- Learn short-term memory, summaries, and compaction.
- Finish Tutorial 3.

### Week 4

- Learn tool design and MCP.
- Finish Tutorial 4.

### Week 5

- Learn orchestration patterns and subagents.
- Finish Tutorial 5.

### Week 6

- Learn tracing, evals, and cost control.
- Finish Tutorial 6.

## Research Basis

- Anthropic, `Effective context engineering for AI agents`, published September 29, 2025, should be treated as the primary conceptual source.
- OpenAI API guides on `Agents`, `Agents SDK`, `Using tools`, `Conversation state`, `Prompt caching`, and `Agent evals` should be treated as the primary implementation sources.
- MCP docs and specification revisions from 2025 should be treated as the primary protocol sources.
- Framework docs should be learned by layer rather than memorized all at once:
  - orchestration: `LangGraph`
  - typed Python agents: `PydanticAI`
  - optimization and eval-driven tuning: `DSPy`
  - retrieval-heavy workflows: `LlamaIndex`
  - product UI delivery: `Vercel AI SDK`

## Rollout Notes

- Start in Python unless your main target is frontend product work, in which case pair Python backends with `Vercel AI SDK` on the UI side.
- Do not start with multi-agent systems. Earn them by first making single-agent context assembly reliable.
- Treat every tutorial as an eval project. If a tutorial does not produce trace data and failure cases, it is incomplete.

# Edit 2 AI Chat 03 RAG Chat 2026-04-19 11:42 Branch: main

## Terminal RAG Chat Request Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant User as User Terminal Input
    participant App as TerminalChatApp<br/>src/03-rag-chat/terminal_app.py
    participant Bot as RAGChatbot<br/>src/03-rag-chat/chatbot.py
    participant Retrieve as KeywordRetrievalStrategy<br/>src/03-rag-chat/retrieval.py
    participant Tokenizer as TiktokenTokenizer<br/>src/03-rag-chat/retrieval.py
    participant Corpus as Document Corpus<br/>src/03-rag-chat/data.py
    participant OpenAI as OpenAI Responses API

    User->>App: Enter question in terminal
    App->>Bot: stream_chat_response(user_text, chat_history)
    Bot->>Bot: build_prompt(user_input, chat_history)
    Bot->>Retrieve: retrieve(user_input, self.documents, limit=3)
    Retrieve->>Tokenizer: tokenize(query)
    Tokenizer->>Tokenizer: encoding.encode(text)
    loop each token id in query
        Tokenizer->>Tokenizer: decode one token id
        Tokenizer->>Tokenizer: strip + lower + keep alnum only
        Tokenizer->>Tokenizer: add compact token into query term set
    end
    Retrieve->>Corpus: iterate documents in build order
    loop each document
        Retrieve->>Retrieve: searchable_text = title + category + text
        Retrieve->>Tokenizer: tokenize(searchable_text)
        Tokenizer->>Tokenizer: build normalized document term set
        Retrieve->>Retrieve: overlap = len(query_terms & doc_terms)
        alt overlap > 0
            Retrieve->>Retrieve: append (overlap, document)
        else overlap == 0
            Retrieve->>Retrieve: skip document
        end
    end
    Retrieve->>Retrieve: sort scored documents by overlap descending
    Retrieve-->>Bot: top matching documents, max 3
    Bot->>Bot: append "Retrieved context:" lines with [id] title (category): text
    Bot->>Bot: append prior conversation turns if present
    Bot->>OpenAI: responses.create(model, input=prompt, stream=True)
    loop streamed response events
        OpenAI-->>Bot: response.output_text.delta
        Bot-->>App: yield text chunk
        App-->>User: print chunk immediately
    end
    App->>App: store User and Assistant turns after stream completes
```

## Retrieval Edge Cases Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Bot as RAGChatbot
    participant Retrieve as KeywordRetrievalStrategy
    participant Tokenizer as TiktokenTokenizer
    participant Docs as Documents

    Bot->>Retrieve: retrieve(query, documents, limit=3)
    Retrieve->>Tokenizer: tokenize(query)
    alt query_terms is empty after normalization
        Tokenizer-->>Retrieve: empty set
        Retrieve-->>Bot: documents[:limit]
        Bot->>Bot: include first three corpus documents as fallback context
    else query_terms not empty
        Tokenizer-->>Retrieve: normalized query term set
        loop each document
            Retrieve->>Docs: compute overlap with document term set
        end
        alt no document has overlap
            Retrieve-->>Bot: []
            Bot->>Bot: omit Retrieved context section entirely
        else one or more documents match
            Retrieve->>Retrieve: descending overlap sort
            Note over Retrieve: tie order stays aligned with original corpus order<br/>because Python sort is stable
            Retrieve-->>Bot: top 3 matched documents
        end
    end
```

## Implementation Notes

- Composition root: `main.py` wires `Settings`, `AsyncOpenAI`, `TiktokenTokenizer`, `KeywordRetrievalStrategy`, `RAGChatbot`, and `TerminalChatApp`.
- Corpus construction is static. `data.py` converts `RAW_DOCUMENTS` into immutable `Document` dataclass instances once during startup.
- Retrieval is purely lexical. There is no embedding index, vector store, reranker, or persistence layer in this tutorial.
- `TiktokenTokenizer.tokenize()` produces a `set[str]` of normalized terms, not an ordered token stream. Duplicate terms are intentionally collapsed before scoring.
- Normalization in `retrieval.py` is strict:
  - token ids come from `tiktoken.encoding_for_model(model)` with fallback to `o200k_base`
  - each token id is decoded individually
  - whitespace is stripped
  - text is lowercased
  - non-alphanumeric characters are removed
  - empty results are discarded
- Document scoring is simple set intersection. A document score is the count of unique normalized terms shared by query and document, not frequency-weighted relevance.
- Document text used for retrieval is assembled from `title`, `category`, and `text`. This means category labels such as `hr` or `security` can directly influence ranking.
- Matching documents are stored as `(overlap, document)` tuples, sorted in descending score order, and truncated to `limit=3`.
- Tie behavior is deterministic relative to corpus order because the sort key only uses overlap and Python sorting is stable.
- Prompt construction is additive:
  - start with the system prompt
  - add retrieved document bullets only if retrieval returns at least one document
  - add full chat history if present
  - append the current `User:` turn and final `Assistant:` cue
- The chat loop keeps conversation history only in process memory inside `TerminalChatApp.chat_history`. Restarting the process drops prior turns.
- Streaming is one-way from the OpenAI Responses API into the terminal. The assistant response is buffered locally only so the completed answer can be stored back into chat history after printing.

## Retrieval Notes

- The retrieval fallback is asymmetric:
  - empty normalized query returns the first three documents
  - non-empty query with zero matches returns no documents
- That asymmetry means punctuation-only or otherwise non-alphanumeric queries still inject default context into the prompt, while specific unmatched queries do not.
- Because scoring is based on unique-term overlap, repeated words in a document do not increase its rank.
- Because each document is retokenized on every user turn, retrieval cost scales linearly with both corpus size and document length for every prompt build.

# Edit 3 RAG Retrieval Hardening 2026-04-19 17:53 Branch: feat/retrieval/embeddings

## Shared Retrieval Text Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Main as build_app<br/>src/03-rag-chat/main.py
    participant Settings as Settings.load<br/>src/config.py
    participant Keyword as KeywordRetrievalStrategy<br/>src/03-rag-chat/retrieval.py
    participant Embed as EmbeddingRetrievalStrategy<br/>src/03-rag-chat/retrieval.py
    participant Serialize as serialize_document_for_retrieval<br/>src/03-rag-chat/retrieval.py
    participant ST as SentenceTransformer
    participant Faiss as FAISS IndexFlatIP

    Main->>Settings: load()
    Settings-->>Main: api_key + chat_model + embedding_model
    alt strategy == "keyword"
        Main->>Keyword: construct(tokenizer)
        loop first retrieval per document id
            Keyword->>Serialize: title + category + text
            Serialize-->>Keyword: shared retrieval text
            Keyword->>Keyword: cache normalized document terms by document id
        end
        Keyword-->>Main: overlap-ranked documents
    else strategy == "embedding"
        Main->>Embed: construct(embedding_model)
        loop build_index(documents)
            Embed->>Serialize: title + category + text
            Serialize-->>Embed: shared retrieval text list
            Embed->>ST: encode(serialized docs, normalize_embeddings=True)
            ST-->>Embed: float32 normalized embeddings
            Embed->>Faiss: reset index and add full embedding matrix
            Embed->>Embed: store indexed document ids in order
        end
        Embed-->>Main: similarity-ranked documents
    end
```

## Low Confidence Embedding Failure Path Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Bot as RAGChatbot<br/>src/03-rag-chat/chatbot.py
    participant Embed as EmbeddingRetrievalStrategy<br/>src/03-rag-chat/retrieval.py
    participant ST as SentenceTransformer
    participant Faiss as FAISS IndexFlatIP

    Bot->>Embed: retrieve(query, documents, limit=3)
    alt index missing or document ids changed
        Embed->>Embed: rebuild full index from current documents
    end
    Embed->>ST: encode([query], normalize_embeddings=True)
    ST-->>Embed: normalized query embedding
    Embed->>Faiss: search(query_embedding, k)
    Faiss-->>Embed: scores + indices
    loop each score/index pair
        alt index == -1 or score < min_similarity
            Embed->>Embed: discard hit
        else score >= min_similarity
            Embed->>Embed: keep matched document
        end
    end
    alt all hits discarded
        Embed-->>Bot: []
        Bot->>Bot: omit Retrieved context block
    else one or more hits survive
        Embed-->>Bot: filtered documents
        Bot->>Bot: include retrieved context bullets
    end
```

## Implementation Notes

- `OPENAI_MODEL` now stays on the chat path while `EMBEDDING_MODEL` is used only when the embedding retrieval strategy is selected.
- `serialize_document_for_retrieval()` is the single retrieval text formatter for both keyword and embedding strategies, so title and category signal are preserved consistently across both paths.
- `KeywordRetrievalStrategy` now caches normalized document term sets by document id instead of retokenizing document text on every query.
- `EmbeddingRetrievalStrategy.build_index()` now recreates the FAISS index on every rebuild and tracks the indexed document id order to avoid stale or duplicated vectors.
- Embedding search uses normalized vectors with `IndexFlatIP`, then applies a `min_similarity` threshold before passing any documents into the prompt.

## Executive Verdict

- Retrieval correctness improved materially. The branch now fixes the chat-vs-embedding model split, prevents stale FAISS state from accumulating across rebuilds, and stops low-confidence embedding hits from being injected as supporting context.
- Residual quality limits remain deliberate: keyword retrieval is still overlap-based rather than BM25-style, and there is still no corpus-level retrieval eval dataset.

## Runtime Check

- `uv run python -m py_compile src/config.py src/03-rag-chat/main.py src/03-rag-chat/retrieval.py tests/test_rag_retrieval.py tests/test_ai_chat_entrypoints.py` passed.
- `uv run pytest tests/test_rag_retrieval.py`, `uv run pytest tests/test_ai_chat_entrypoints.py`, and `make test` were started in the sandbox but did not produce a usable completion signal before timeout/TTY limitations. The test intent is documented below; final PR notes should call out that the static compile check completed while live pytest confirmation remained inconclusive in this environment.

## Scoring Scale

- `Overall`, `Useful`, `Critical`, `Design`: `1` low, `5` high.
- `Redundant`: `1` not redundant, `5` highly redundant.

## Per-Test Review

### Retrieval Regression Suite

| Ref | De Facto Test Name | What it proves | Overall | Useful | Critical | Redundant | Design | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | `test_settings_uses_separate_chat_and_embedding_models` | The runtime no longer conflates the OpenAI chat model with the Hugging Face embedding model identifier. | 5 | 5 | 5 | 1 | 4 | Directly covers the original production breakage and keeps the config contract explicit. |
| R2 | `test_serialize_document_for_retrieval_includes_all_relevant_fields` | Shared retrieval text includes `title`, `category`, and `text` for both retrieval strategies. | 4 | 4 | 4 | 1 | 4 | Small but load-bearing because keyword and embedding retrieval now rely on the same serialization helper. |
| R3 | `test_keyword_retrieval_uses_cached_document_terms` | Keyword retrieval reuses cached normalized term sets instead of re-tokenizing every document on repeat queries. | 4 | 4 | 3 | 1 | 4 | Good regression coverage for the performance-oriented behavior change without over-specifying ranking internals. |
| R4 | `test_keyword_retrieval_refreshes_cache_when_document_text_changes` | Keyword retrieval invalidates cached document terms when a document keeps the same id but its serialized retrieval text changes. | 5 | 5 | 4 | 1 | 5 | Covers the load-bearing stale-cache edge case for long-lived strategy instances. |
| R5 | `test_embedding_retrieval_indexes_shared_document_text` | Embedding indexing uses the same serialized document text as keyword retrieval, preserving title/category signal. | 5 | 5 | 4 | 1 | 4 | Important parity check between the two retrieval paths. |
| R6 | `test_embedding_retrieval_resets_index_on_rebuild` | FAISS state is reset on rebuild so stale vectors do not survive across corpus changes. | 5 | 5 | 5 | 1 | 5 | Most critical correctness guard in the new embedding path. |
| R7 | `test_embedding_retrieval_rebuilds_when_document_text_changes` | Embedding retrieval rebuilds when indexed documents keep the same id but their serialized retrieval text changes. | 5 | 5 | 5 | 1 | 5 | Prevents silent reuse of stale vectors when document content changes in place. |
| R8 | `test_embedding_retrieval_returns_empty_for_low_similarity_queries` | Low-confidence embedding matches are dropped instead of being injected into the prompt as false support. | 5 | 5 | 5 | 1 | 5 | Protects the grounded-answer contract at the prompt boundary, not just internal ranking semantics. |

# Edit 4 Keyword Retrieval Cache Tradeoffs 2026-04-20 14:28 Branch: feat/retrieval/embeddings

## Keyword Cache Request Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Bot as RAGChatbot<br/>src/03-rag-chat/chatbot.py
    participant Keyword as KeywordRetrievalStrategy<br/>src/03-rag-chat/retrieval.py
    participant Serialize as serialize_document_for_retrieval<br/>src/03-rag-chat/retrieval.py
    participant Tokenizer as TiktokenTokenizer<br/>src/03-rag-chat/retrieval.py
    participant Cache as _document_terms<br/>in-memory dict

    Bot->>Keyword: retrieve(query, documents, limit=3)
    Keyword->>Tokenizer: tokenize(query)
    loop each document
        Keyword->>Serialize: title + category + text
        Serialize-->>Keyword: serialized_document
        Keyword->>Cache: get(document.id)
        alt cached serialized text matches
            Cache-->>Keyword: cached term set
            Keyword->>Keyword: reuse tokenized document terms
        else cache missing or serialized text changed
            Cache-->>Keyword: miss or stale entry
            Keyword->>Tokenizer: tokenize(serialized_document)
            Tokenizer-->>Keyword: document term set
            Keyword->>Cache: store(document.id -> (serialized_document, term_set))
        end
        Keyword->>Keyword: compute query/document overlap
    end
    Keyword-->>Bot: overlap-ranked documents
```

## Cache Value Threshold Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant User as User traffic
    participant App as App process
    participant Keyword as KeywordRetrievalStrategy
    participant CPU as CPU time

    alt tiny corpus or one-off query burst
        User->>App: 1 to few searches
        App->>Keyword: build strategy and answer
        Keyword->>CPU: tokenize each document once or twice
        Note over App,CPU: cache benefit is marginal
    else repeated queries against same in-memory corpus
        User->>App: many searches in same process
        App->>Keyword: reuse same strategy instance
        Keyword->>CPU: avoid re-tokenizing unchanged documents
        Note over App,CPU: cache benefit compounds with query volume and corpus size
    else document corpus mutates frequently
        User->>App: searches while documents change
        App->>Keyword: same ids, new text
        Keyword->>CPU: invalidate stale entries by serialized text mismatch
        Note over App,CPU: correctness preserved, cache hit rate drops
    end
```

## Implementation Notes

- The cache solves repeated document-tokenization work, not retrieval quality. It exists to avoid recomputing the same normalized token set for unchanged documents on every query.
- The expensive part being avoided is the repeated `tokenizer.tokenize(serialized_document)` call for every document on every request. In this toy app that cost is modest; in a larger corpus or higher-query process it becomes steady CPU overhead.
- The fetch rule is exact-match invalidation, not a threshold:
  - reuse cached terms when `document.id` exists in `_document_terms` and the cached serialized text equals the current serialized text
  - recompute when the id is absent or the serialized text changed
- The cache is process-local and in-memory only:
  - no disk persistence
  - no TTL
  - no size-based eviction
  - no cross-worker sharing
- The practical win appears only when the same `KeywordRetrievalStrategy` instance serves multiple queries over mostly stable documents.

## Production Examples

- Internal policy bot with a few hundred static HR/IT/security documents and many employee questions per app process. Each question reuses the same document set, so cached document terms save repeated normalization work across every query.
- Customer support workspace assistant where agents ask many follow-up questions against the same knowledge base during one shift. Query text changes, but most document text does not, so the cache trades a small amount of RAM for lower repeated CPU cost.
- Multi-tenant RAG worker that keeps one corpus in memory per tenant for minutes or hours. The cache helps when each tenant has bursts of repeated searches and the worker does not rebuild state every request.
- It matters much less for a CLI demo where a user asks one question and exits, or for a serverless handler that rebuilds the process on each request.

## When You Do Not Need It

- One-off scripts, notebooks, or CLIs where the process serves very few queries before exiting.
- Very small corpora where re-tokenizing every document is operationally irrelevant and code simplicity matters more than CPU savings.
- Systems where documents are changing so frequently that cache hits are rare and the invalidation logic buys little.
- Architectures that already precompute or externalize lexical features elsewhere, such as a search engine or a BM25 index.

## Alternative Decisions And Tradeoffs

- Keep no cache:
  - simplest implementation
  - lowest memory usage
  - best when corpus size and query volume are both small
- In-memory per-process cache:
  - cheap and simple
  - no network hop
  - duplicated across workers and lost on restart
- Precomputed lexical index:
  - better when corpus is larger and retrieval is core product behavior
  - more upfront complexity and rebuild logic
  - usually a better long-term choice than hand-rolled overlap scoring
- External search backend:
  - highest operational complexity
  - strongest fit when you need ranking quality, filtering, facets, and multi-worker consistency
  - overkill for tutorial-scale corpora

## Design Guidance

- Use the current cache when:
  - documents are mostly stable
  - the same process serves repeated queries
  - you want a low-complexity optimization without adding infrastructure
- Skip it when:
  - the product is small enough that the repeated tokenization cost is noise
  - readability matters more than a micro-optimization
- Move to a real lexical index when:
  - query volume grows
  - corpus size grows beyond tutorial scale
  - ranking quality becomes more important than avoiding repeated tokenization

# Edit 5 Hybrid BM25 Retrieval 2026-04-20 16:45 Branch: feat/retrieval/hybrid

## Hybrid Retrieval Request Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant User as User Terminal Input
    participant App as TerminalChatApp<br/>ai-chat/03-rag-chat/terminal_app.py
    participant Bot as RAGChatbot<br/>ai-chat/03-rag-chat/chatbot.py
    participant Hybrid as HybridRetrievalStrategy<br/>ai-chat/03-rag-chat/retrieval.py
    participant BM25 as BM25RetrievalStrategy<br/>ai-chat/03-rag-chat/retrieval.py
    participant Dense as EmbeddingRetrievalStrategy<br/>ai-chat/03-rag-chat/retrieval.py
    participant CE as CrossEncoderReranker<br/>ai-chat/03-rag-chat/retrieval.py
    participant OpenAI as OpenAI Responses API

    User->>App: Enter question in terminal
    App->>Bot: stream_chat_response(user_text, chat_history)
    Bot->>Hybrid: retrieve(user_input, self.documents, limit=3)
    par lexical recall
        Hybrid->>BM25: retrieve(query, documents, candidate_k)
        BM25->>BM25: tokenize serialized docs with tiktoken-normalized splitter
        BM25->>BM25: rebuild BM25 index if document snapshot changed
        BM25-->>Hybrid: ranked lexical candidates
    and semantic recall
        Hybrid->>Dense: retrieve(query, documents, candidate_k)
        Dense->>Dense: rebuild FAISS index if document snapshot changed
        Dense-->>Hybrid: ranked dense candidates
    end
    Hybrid->>Hybrid: reciprocal-rank-fuse candidate lists by document id
    Hybrid->>CE: rerank(query, fused_candidates, limit)
    CE-->>Hybrid: top reranked documents
    Hybrid-->>Bot: final top documents
    Bot->>Bot: append Retrieved context bullets
    Bot->>OpenAI: responses.create(model, input=prompt, stream=True)
    OpenAI-->>App: streamed output deltas
    App-->>User: print response
```

## Reranker Failure Path Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Bot as RAGChatbot
    participant Hybrid as HybridRetrievalStrategy
    participant BM25 as BM25RetrievalStrategy
    participant Dense as EmbeddingRetrievalStrategy
    participant CE as CrossEncoderReranker

    Bot->>Hybrid: retrieve(query, documents, limit=3)
    Hybrid->>BM25: lexical candidates
    Hybrid->>Dense: dense candidates
    Hybrid->>Hybrid: reciprocal-rank fusion
    Hybrid->>CE: rerank(query, fused_candidates, limit)
    alt reranker returns scores
        CE-->>Hybrid: reranked top documents
        Hybrid-->>Bot: reranked documents
    else reranker raises or is unavailable
        CE-->>Hybrid: exception
        Hybrid->>Hybrid: keep fused pre-rerank order
        Hybrid-->>Bot: fallback documents
    end
```

## Keyword vs BM25 Decision Matrix

| Dimension | Keyword Overlap | BM25 |
| --- | --- | --- |
| Ranking signal | Unique-term overlap only | Term frequency, inverse document frequency, and document-length normalization |
| Tokenization source | Shared tiktoken normalization | Same shared tiktoken normalization via custom `bm25s` splitter |
| Query/document cache | In-memory term-set cache | Full lexical index rebuild when serialized corpus changes |
| Repeated-word sensitivity | Repeated words do not help rank | Repeated informative terms can improve rank |
| Small-corpus simplicity | Simplest baseline | Slightly heavier but still local and dependency-light |
| Best role in this tutorial | Baseline and teaching reference | Real lexical retriever for hybrid recall |

## Implementation Notes

- `main.py` now supports `keyword`, `bm25`, `embedding`, and `hybrid` while keeping `keyword` as the default CLI path.
- `config.py` now loads `RERANKER_MODEL`, defaulting to `cross-encoder/ms-marco-MiniLM-L6-v2`.
- `retrieval.py` now shares one retrieval serialization function across keyword, BM25, dense retrieval, and reranking so title/category signal stays aligned.
- `TiktokenTokenizer` now exposes both:
  - a unique-token set for the legacy keyword strategy
  - an ordered token sequence for BM25 indexing and querying
- `BM25RetrievalStrategy` uses `bm25s` with a custom splitter backed by the same tiktoken normalization rules used by the keyword baseline.
- `EmbeddingRetrievalStrategy` keeps the existing sentence-transformer embedding model and FAISS cosine-similarity search semantics.
- `HybridRetrievalStrategy` fuses BM25 and dense candidate lists with reciprocal rank fusion before final cross-encoder reranking.
- The reranker failure policy is fail-open. If local reranking raises, the app still answers using fused pre-rerank candidates instead of aborting the turn.
- `cross-encoder/ms-marco-MiniLM-L6-v2` was chosen as the default local reranker because it is small, widely used, and integrates directly through `sentence_transformers.CrossEncoder`.

## Executive Verdict

- Retrieval quality now has a real progression:
  - `keyword` remains the simplest lexical baseline
  - `bm25` provides a stronger local lexical retriever
  - `embedding` preserves dense-only comparison
  - `hybrid` is the highest-quality path because it combines recall from BM25 and dense search, then sharpens final precision with reranking
- The main tradeoff is local complexity and runtime cost. Hybrid retrieval adds a BM25 index, a dense index, and a cross-encoder scoring pass, which is justified for comparison/tutorial value but would be unnecessary for the smallest baseline path.

## Runtime Check

- `uv add bm25s` completed successfully and updated the project dependency set.
- `uv run python -m py_compile ai-chat/config.py ai-chat/03-rag-chat/main.py ai-chat/03-rag-chat/retrieval.py tests/test_rag_retrieval.py tests/test_ai_chat_entrypoints.py` passed.
- `uv run pytest ...` did not produce a usable completion signal in this environment, so verification was completed with direct Python harness execution of the retrieval assertions and the entrypoint subprocess checks instead.

## Scoring Scale

- `Overall`, `Useful`, `Critical`, `Design`: `1` low, `5` high.
- `Redundant`: `1` not redundant, `5` highly redundant.

## Per-Test Review

### Retrieval Regression Suite

| Ref | De Facto Test Name | What it proves | Overall | Useful | Critical | Redundant | Design | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | `test_tiktoken_tokenizer_returns_bm25_sequence_tokens` | BM25 uses the same tiktoken-driven normalization family as the keyword baseline while preserving repeated token order. | 4 | 4 | 4 | 1 | 4 | Important contract test because tokenizer drift would quietly invalidate the keyword-vs-BM25 comparison. |
| H2 | `test_bm25_retrieval_indexes_shared_document_text` | BM25 indexes the same serialized retrieval text used everywhere else. | 5 | 5 | 4 | 1 | 4 | High-signal parity check across lexical, dense, and rerank layers. |
| H3 | `test_bm25_retrieval_rebuilds_when_document_text_changes` | BM25 does not reuse stale lexical state across corpus mutations. | 5 | 5 | 5 | 1 | 5 | Load-bearing because the BM25 tokenizer vocabulary and index must stay aligned. |
| H4 | `test_hybrid_retrieval_reranks_fused_candidates_with_cross_encoder` | Final hybrid ordering is controlled by the reranker rather than whichever first-stage retriever happened to rank a candidate earlier. | 5 | 5 | 5 | 1 | 5 | Core proof that the new architecture is actually rerank-first at the final selection boundary. |
| H5 | `test_hybrid_retrieval_falls_back_to_fused_order_when_reranker_raises` | Hybrid retrieval continues serving grounded context when local reranking fails. | 5 | 5 | 5 | 1 | 5 | Covers the chosen fail-open production behavior directly. |
| H6 | `test_build_app_supports_bm25_and_hybrid` | `main.py` wires the new strategies and eager index builds correctly at the composition root. | 4 | 4 | 4 | 1 | 4 | Good integration guard for the CLI surface without forcing real model downloads in test. |
