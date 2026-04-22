PYTHON := uv run python
PYTEST := uv run pytest

.PHONY: test test-all test-01-chat-entrypoints test-03-rag-retrieval test-04-eval-harness test-90-live-happy-paths test-live-happy-paths run-history run-stream run-rag run-evals

test: test-all

test-all: test-01-chat-entrypoints test-03-rag-retrieval test-04-eval-harness

test-01-chat-entrypoints:
	$(PYTEST) tests/test_ai_chat_entrypoints.py

test-03-rag-retrieval:
	$(PYTEST) tests/test_rag_retrieval.py

test-04-eval-harness:
	$(PYTEST) tests/test_eval_harness.py

test-90-live-happy-paths:
	$(PYTEST) tests/e2e/test_live_happy_paths.py

test-live-happy-paths: test-90-live-happy-paths

run-history:
	uv run src/01-chat-app-with-history.py

run-stream:
	uv run src/02-chat-app-with-stream.py

run-rag:
	uv run src/03-rag-chat/main.py

run-evals:
	uv run src/04-evals/main.py
