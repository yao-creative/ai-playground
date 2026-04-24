from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    category: str
    text: str


class RetrievalStrategy(Protocol):
    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        """Return the most relevant documents for a query."""


class Tokenizer(Protocol):
    def tokenize(self, text: str) -> set[str]:
        """Return a normalized token set for retrieval."""
