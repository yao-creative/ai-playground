PYTHON := uv run python
PYTEST := uv run pytest

.PHONY: test test-chat test-rag test-live-happy-paths run-history run-stream run-rag

test: test-chat test-rag

test-chat:
	$(PYTEST) tests/test_ai_chat_entrypoints.py

test-rag:
	$(PYTEST) tests/test_rag_retrieval.py

test-live-happy-paths:
	$(PYTEST) tests/e2e/test_live_happy_paths.py

run-history:
	uv run src/01-chat-app-with-history.py

run-stream:
	uv run src/02-chat-app-with-stream.py

run-rag:
	uv run src/03-rag-chat/main.py
