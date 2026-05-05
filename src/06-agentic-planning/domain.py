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
        """Return relevant documents for the query."""


class Tokenizer(Protocol):
    def tokenize(self, text: str) -> set[str]:
        """Return normalized token set for retrieval."""

    def tokenize_to_sequence(self, text: str) -> list[str]:
        """Return normalized token sequence for retrieval backends that need order."""
