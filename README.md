# `AI PlayGround, Zero to Hero`

A series of experiments of playing with AI chat in varying complexities of design.

## References

Small terminal-based AI chat playground for experimenting with:

- basic chat loops
- streaming responses
- simple retrieval-augmented generation (RAG)
- eval-first development habits
- lightweight agent and context-engineering patterns

This directory is intentionally small. The goal is not to ship a production framework. The goal is to keep the code easy to change while playing with ideas from:

- [https://hamel.dev/blog/posts/evals/](https://hamel.dev/blog/posts/evals/)
- [https://jxnl.co/writing/2024/02/28/levels-of-complexity-rag-applications/](https://jxnl.co/writing/2024/02/28/levels-of-complexity-rag-applications/)
- [https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/#tier-2-primary-rag-relationships](https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/#tier-2-primary-rag-relationships) 
- [https://www.sh-reya.com/blog/ai-engineering-flywheel/#1-evaluation-defining-success-metrics](https://www.sh-reya.com/blog/ai-engineering-flywheel/#1-evaluation-defining-success-metrics)
- [https://eugeneyan.com/writing/evals/](https://eugeneyan.com/writing/evals/)
- [https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [https://www.anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)
- [https://www.anthropic.com/engineering/managed-agents](https://www.anthropic.com/engineering/managed-agents)

## Overview

This folder is organized as a numbered progression from basic chat to simple retrieval:

1. `01-chat-app-with-history.py`
  Minimal terminal chat loop with conversation history included in the prompt.
2. `02-chat-app-with-stream.py`
  Same chat pattern, but streams tokens to the terminal for better UX.
3. `03-rag-chat/main.py`
  Retrieval-augmented chat that loads a fixed document set, retrieves relevant context, and answers with that context included in the prompt.

The numbering is intentional:

- `01` Smallest useful terminal chat loop
- `02` Streamed Response
- `03` RAG-ed Chat (Builder + Strategy Pattern)
  - (Hybrid - Semantic, BM25)
  - Semantic
  - Keyword (Full text search. Jaccard)
- `04` Eval Harnesses
- `05` Agentic RAG
- `06` Agentic Planning (Plan -> Draft -> Review -> Redraft)
- `07` Big Patent App

`08+` Future experiments

## Features

Across the numbered examples, this playground currently includes:

- terminal-first chat loops with `bye`/`exit`/`quit` handling
- OpenAI Responses API integration
- conversation history in the prompt
- streamed text output in the streaming app
- a tiny RAG example with an in-memory document set
- keyword retrieval using model-aware tokenization via `tiktoken`
- optional embedding retrieval using `sentence-transformers` and `faiss`
- deterministic smoke tests for all runnable entrypoints
- opt-in live happy-path tests that hit the real model APIs

## Numbered Apps

1. `01-chat-app-with-history.py`
  Features:
  - synchronous terminal chat loop
  - full chat history appended to each prompt
  - simplest place to experiment with prompt shape and memory handling
2. `02-chat-app-with-stream.py`
  Features:
  - async OpenAI client
  - streaming assistant output in real time
  - same history-based prompt structure as `01`
3. `03-rag-chat/main.py`
  Features:
  - loads a fixed in-memory document set
  - retrieves documents with simple keyword overlap using model tokenization
  - optionally retrieves documents with sentence embeddings plus FAISS
  - appends retrieved context to the prompt
  - streams the answer back to the terminal
  - returns no retrieved docs when embedding similarity is too weak, instead of forcing irrelevant context
4. `05-agentic-rag/main.py`
  Features:
  - single-agent bounded tool loop over the same fixed document corpus
  - local retrieval tools: search document snippets and read a full document
  - model chooses when to search, inspect, and finish
  - grounded answers include cited document ids
  - unsupported questions end with a clear insufficient-support answer
5. `06-agentic-planning/main.py`
  Features:
  - standalone modular pipeline: evidence collection, planner, drafter, reviewer, redrafter
  - one-pass redraft loop with reviewer gate before finalization
  - grounded-answer invariant: supported answers must include citations
  - fallback to unsupported response when review fails after redraft budget

The current RAG implementation is deliberately simple. That makes it a good place to test changes one variable at a time.

## Setup

### 1. Create `.env`

Create a `.env` file at the repo root:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5-mini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

`OPENAI_MODEL` is used for chat generation. `EMBEDDING_MODEL` is used only by the embedding retrieval path in `03-rag-chat`.

### 2. Install dependencies

Install dependencies:

```bash
uv sync
```

### 3. Run the numbered apps

Run the examples from the repo root:

```bash
make run-history
make run-stream
make run-rag
make run-agentic-rag
make run-agentic-planning
```

To run the RAG app with embedding retrieval explicitly:

```bash
uv run src/03-rag-chat/main.py --strategy embedding
```

### 4. Run tests

Run the smoke tests:

```bash
make test-all
```

Run the opt-in live happy-path e2e suite:

```bash
RUN_LIVE_TESTS=1 make test-90-live-happy-paths
```

Available test targets:

```bash
make test-01-chat-entrypoints
make test-03-rag-retrieval
make test-04-eval-harness
make test-05-agentic-rag
make test-06-agentic-planning
make test-all
RUN_LIVE_TESTS=1 make test-90-live-happy-paths
```

Live happy-path tests reuse the normal app config from `.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `EMBEDDING_MODEL`
- `RUN_LIVE_TESTS=1`

The suite sends one real message through:

- `01-chat-app-with-history.py`
- `02-chat-app-with-stream.py`
- `03-rag-chat/main.py --strategy keyword`
- `03-rag-chat/main.py --strategy embedding`

It asserts startup, a non-empty assistant response, and clean exit. It is intentionally opt-in because it can incur OpenAI usage and may also trigger embedding-model download/setup in the embedding RAG path.

## How to use this playground

Think of the three scripts as a progression:

- `01`: single-call chat with memory
- `02`: better UX through streaming
- `03`: basic retrieval and context assembly

From there, the next useful step is not "add more complexity everywhere." The next useful step is to introduce measurement and controlled iteration.

## Concepts to play with

### 1. Evals before prompt thrash

The main lesson from the evals references is that fast iteration depends on having cheap, repeatable ways to measure behavior. Instead of only tweaking prompts, define expected behaviors and failure modes, then run them often.

Good experiments for this repo:

- add prompt-level assertions for obvious failures
- collect example user questions and expected properties of answers
- turn recurring failures into regression tests
- separate fast local checks from slower model-graded checks

Examples of simple checks:

- answer should not invent policy details not present in retrieved docs
- answer should mention uncertainty when retrieval has weak support
- answer should cite the relevant policy title or document id
- answer should refuse to answer questions outside available context

### 2. RAG as a ladder of complexity

The current `03-rag-chat` example is near the low-complexity end:

- static documents
- lexical retrieval
- prompt stuffing of top matches
- no query rewriting
- no reranking
- no chunking pipeline
- no citations or structured outputs

That is a feature, not a limitation. It gives you a stable baseline to compare against as you try:

- chunking instead of full-document retrieval
- embeddings instead of keyword overlap
- reranking after retrieval
- query transformation
- answer grounding or citation formatting
- retrieval diagnostics like recall@k on a labeled set

### 3. Data flywheel mindset

A useful way to evolve this project is:

1. define success metrics
2. capture failures and interesting traces
3. turn failures into labeled examples
4. update prompts, retrieval, or code
5. rerun evals

That loop is the real product here. The scripts are just the substrate.

### 4. Task-specific evals over vague "quality"

Avoid one fuzzy metric called "good response." Use narrower measurements:

- retrieval hit rate
- groundedness / factual support
- completeness
- refusal correctness
- latency
- cost

For binary or categorical checks, track precision and recall instead of only accuracy. In practice, false positives and false negatives often matter differently.

### 5. Context engineering

This repo is also a good place to practice context engineering:

- keep the system prompt short and direct
- include only the highest-signal retrieved context
- avoid stuffing too much history into every turn
- decide what belongs in instructions vs retrieved facts vs conversation state

As you add features, treat context as a limited budget. More tokens are not automatically better.

### 6. Simple workflows before "full agents"

Before building an autonomous agent loop, it is usually better to try smaller patterns:

- prompt chaining
- routing
- parallel evaluations
- evaluator-optimizer loops

This repo can support those patterns incrementally without a major rewrite.

## Suggested experiment roadmap

If you want a concrete sequence, this is a sensible order:

1. Add a tiny eval dataset for `03-rag-chat`
  Store questions, expected documents, and expected answer properties.
2. Add retrieval evals
  Measure whether the correct document appears in the top `k`.
3. Add answer evals
  Start with deterministic checks, then add model-graded checks later.
4. Log traces
  Save the user query, retrieved docs, final prompt, and model answer for inspection.
5. Upgrade retrieval
  Compare keyword retrieval vs embeddings on the same eval set.
6. Add structured answers
  For example: answer, confidence, supporting document ids, and abstain flag.
7. Add an evaluator-optimizer loop
  Generate an answer, critique it against explicit criteria, then revise once.
8. Add a narrow agent workflow only if the evals justify it
  For example: route between "chat only" and "retrieve then answer".

## Good first extensions

- `evals/qa.jsonl` for curated test cases
- `tests/test_rag_retrieval.py` for retrieval behavior
- `tests/test_rag_grounding.py` for grounding assertions
- `src/03-rag-chat/evals.py` for offline evaluation runs
- `src/03-rag-chat/tracing.py` for prompt and retrieval logs
- `src/03-rag-chat/embeddings_retrieval.py` for A/B comparison

## Design principle

Keep each change inspectable.

If you change retrieval, keep the prompt constant.
If you change the prompt, keep retrieval constant.
If you add an evaluator, do not also redesign the whole app in the same step.

This repo is most useful when it stays small enough that you can explain every behavior change.
