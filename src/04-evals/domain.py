from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    category: str
    text: str


@dataclass(frozen=True)
class EvalExample:
    id: str
    question: str
    expected_answer_notes: str
    gold_doc_ids: list[str]
    category: str


@dataclass(frozen=True)
class RetrievedDoc:
    id: str
    title: str
    category: str
    text: str
    rank: int
    score: float | None = None


@dataclass(frozen=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    prompt: str
    model: str
    usage: Usage


@dataclass(frozen=True)
class ScoreResult:
    name: str
    passed: bool
    score: float
    comment: str


@dataclass
class RunRecord:
    example_id: str
    question: str
    category: str
    expected_answer_notes: str
    gold_doc_ids: list[str]
    retrieved_docs: list[RetrievedDoc]
    final_prompt: str
    answer: str
    latency_ms: float
    model: str
    usage: Usage
    scorer_results: list[ScoreResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Protocols are the key modular seam: you can swap retrieval, answering, or scoring
# strategies without changing the orchestration code in main.py.
class Retriever(Protocol):
    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[RetrievedDoc]:
        """Return ranked context candidates for one question."""


class Answerer(Protocol):
    def answer(self, question: str, retrieved_docs: list[RetrievedDoc]) -> AnswerResult:
        """Generate one grounded answer from the retrieved context."""


class Scorer(Protocol):
    def score(self, example: EvalExample, run_record: RunRecord) -> ScoreResult:
        """Score a single run record for one eval facet."""
