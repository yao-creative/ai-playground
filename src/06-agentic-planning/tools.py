from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from models import ToolCall, ToolResult


@dataclass(frozen=True)
class ToolSpec:
    name: str
    prompt_schema: str
    validator_name: str
    executor_name: str


class DocumentTools:
    def __init__(self, documents: Iterable[Any], retrieval_strategy) -> None:
        self.documents = list(documents)
        self.retrieval_strategy = retrieval_strategy
        self._documents_by_id = {document.id: document for document in self.documents}
        self._tool_specs = self._register_tools()
        self._tool_specs_by_name = {spec.name: spec for spec in self._tool_specs}

    def _register_tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="search_documents",
                prompt_schema='{"tool_name":"search_documents","arguments":{"query":"string","limit":1-5}}',
                validator_name="_validate_search_documents_args",
                executor_name="_run_search_documents",
            ),
            ToolSpec(
                name="read_document",
                prompt_schema='{"tool_name":"read_document","arguments":{"doc_id":"doc-###"}}',
                validator_name="_validate_read_document_args",
                executor_name="_run_read_document",
            ),
        ]

    def list_tool_prompt_schemas(self) -> list[str]:
        return [f"- {spec.prompt_schema}" for spec in self._tool_specs]

    def validate_action(self, tool_name: str, arguments: dict[str, Any]) -> ToolCall:
        spec = self._tool_specs_by_name.get(tool_name)
        if spec is None:
            raise ValueError(f"Unsupported tool: {tool_name}")
        validator = getattr(self, spec.validator_name)
        normalized_arguments = validator(arguments)
        return ToolCall(tool_name=tool_name, arguments=normalized_arguments)

    def execute(self, tool_call: ToolCall) -> ToolResult:
        spec = self._tool_specs_by_name.get(tool_call.tool_name)
        if spec is None:
            return ToolResult(tool_name=tool_call.tool_name, payload={}, error="Unknown tool")
        executor = getattr(self, spec.executor_name)
        return executor(**tool_call.arguments)

    def _validate_search_documents_args(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("search_documents requires non-empty string argument 'query'.")

        limit_raw = arguments.get("limit", 3)
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("search_documents argument 'limit' must be an integer.") from error

        return {"query": query.strip(), "limit": max(1, min(limit, 5))}

    def _validate_read_document_args(self, arguments: dict[str, Any]) -> dict[str, Any]:
        doc_id = arguments.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError("read_document requires non-empty string argument 'doc_id'.")
        return {"doc_id": doc_id.strip()}

    def _run_search_documents(self, query: str, limit: int = 3) -> ToolResult:
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

    def _run_read_document(self, doc_id: str) -> ToolResult:
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
