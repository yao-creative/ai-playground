from collections.abc import Iterable
from typing import Any

from models import ToolCall, ToolResult


class DocumentTools:
    def __init__(self, documents: Iterable[Any], retrieval_strategy) -> None:
        self.documents = list(documents)
        self.retrieval_strategy = retrieval_strategy
        self._documents_by_id = {document.id: document for document in self.documents}

    def execute(self, tool_call: ToolCall) -> ToolResult:
        if tool_call.tool_name == "search_documents":
            return self.search_documents(**tool_call.arguments)
        if tool_call.tool_name == "read_document":
            return self.read_document(**tool_call.arguments)
        return ToolResult(
            tool_name=tool_call.tool_name,
            payload={},
            error=f"Unknown tool: {tool_call.tool_name}",
        )

    def search_documents(self, query: str, limit: int = 3) -> ToolResult:
        safe_limit = max(1, min(int(limit), 5))
        documents = self.retrieval_strategy.retrieve(query, self.documents, limit=safe_limit)
        payload = {
            "query": query,
            "results": [
                {
                    "doc_id": document.id,
                    "title": document.title,
                    "category": document.category,
                    "snippet": self._build_snippet(document),
                }
                for document in documents
            ],
        }
        return ToolResult(tool_name="search_documents", payload=payload)

    def read_document(self, doc_id: str) -> ToolResult:
        document = self._documents_by_id.get(doc_id)
        if document is None:
            return ToolResult(
                tool_name="read_document",
                payload={"doc_id": doc_id},
                error=f"Document not found: {doc_id}",
            )

        payload = {
            "doc_id": document.id,
            "title": document.title,
            "category": document.category,
            "text": document.text,
        }
        return ToolResult(tool_name="read_document", payload=payload)

    def _build_snippet(self, document: Any, max_words: int = 18) -> str:
        words = f"{document.title} {document.category} {document.text}".split()
        return " ".join(words[:max_words])
