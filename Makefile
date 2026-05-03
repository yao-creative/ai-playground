PYTHON := uv run python
PYTEST := uv run pytest

.PHONY: test test-all test-chat test-rag test-evals test-01-chat-entrypoints test-03-rag-retrieval test-04-eval-harness test-05-agentic-rag test-90-live-happy-paths test-live-happy-paths run-history run-stream run-rag run-agentic-rag run-evals run-big-patent-preview run-big-patent-stats run-big-patent-jsonl

test: test-all

test-all: test-01-chat-entrypoints test-03-rag-retrieval test-04-eval-harness test-05-agentic-rag

test-01-chat-entrypoints:
	$(PYTEST) tests/test_ai_chat_entrypoints.py

test-chat: test-01-chat-entrypoints

test-03-rag-retrieval:
	$(PYTEST) tests/test_rag_retrieval.py

test-rag: test-03-rag-retrieval

test-04-eval-harness:
	$(PYTEST) tests/test_eval_harness.py

test-evals: test-04-eval-harness

test-05-agentic-rag:
	$(PYTEST) tests/test_agentic_rag.py

test-90-live-happy-paths:
	$(PYTEST) tests/e2e/test_live_happy_paths.py

test-live-happy-paths: test-90-live-happy-paths

run-history:
	uv run src/01-chat-app-with-history.py

run-stream:
	uv run src/02-chat-app-with-stream.py

run-rag:
	uv run src/03-rag-chat/main.py

run-agentic-rag:
	uv run src/05-agentic-rag/main.py

run-evals:
	uv run src/04-evals/main.py

run-big-patent-preview:
	uv run python src/06-big-patent-app/main.py --config $${CONFIG:-all} --split $${SPLIT:-train} --limit $${LIMIT:-20} --mode preview --preview-count $${PREVIEW_COUNT:-3}

run-big-patent-stats:
	uv run python src/06-big-patent-app/main.py --config $${CONFIG:-all} --split $${SPLIT:-train} --limit $${LIMIT:-100} --mode stats

run-big-patent-jsonl:
	uv run python src/06-big-patent-app/main.py --config $${CONFIG:-all} --split $${SPLIT:-train} --limit $${LIMIT:-10000} --mode jsonl --out $${OUT:-data/big_patent_v0_sample.jsonl}
