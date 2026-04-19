PYTHON := uv run python
PYTEST := uv run pytest

.PHONY: test test-chat run-history run-stream run-rag

test: test-chat

test-chat:
	$(PYTEST) tests/test_ai_chat_entrypoints.py

run-history:
	uv run ai-chat/01-chat-app-with-history.py

run-stream:
	uv run ai-chat/02-chat-app-with-stream.py

run-rag:
	uv run ai-chat/03-rag-chat/main.py
