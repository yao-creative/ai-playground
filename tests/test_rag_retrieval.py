import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CHAT_DIR = REPO_ROOT / "src"
RAG_CHAT_DIR = AI_CHAT_DIR / "03-rag-chat"

for path in (AI_CHAT_DIR, RAG_CHAT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from config import Settings
from domain import Document
from retrieval import (
    EmbeddingRetrievalStrategy,
    KeywordRetrievalStrategy,
    serialize_document_for_retrieval,
)


class FakeTokenizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def tokenize(self, text: str) -> set[str]:
        self.calls.append(text)
        return {token.lower() for token in text.split()}


class FakeSentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.calls: list[list[str]] = []

    def get_sentence_embedding_dimension(self) -> int:
        return 2

    def encode(
        self,
        inputs,
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ):
        assert convert_to_numpy is True
        assert normalize_embeddings is True
        self.calls.append(list(inputs))

        vectors = []
        for text in inputs:
            lower = text.lower()
            if "refund" in lower:
                vectors.append([1.0, 0.0])
            elif "vacation" in lower:
                vectors.append([0.0, 1.0])
            elif "office" in lower:
                vectors.append([0.7, 0.7])
            else:
                vectors.append([0.0, 0.0])

        array = np.asarray(vectors, dtype="float32")
        if normalize_embeddings:
            norms = np.linalg.norm(array, axis=1, keepdims=True)
            norms[norms == 0.0] = 1.0
            array = array / norms
        return array


def test_settings_uses_separate_chat_and_embedding_models(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    settings = Settings.load()

    assert settings.chat_model == "gpt-5-mini"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_serialize_document_for_retrieval_includes_all_relevant_fields() -> None:
    document = Document(
        id="doc-1",
        title="Refund Policy",
        category="finance",
        text="Submit receipts within 30 days.",
    )

    assert serialize_document_for_retrieval(document) == (
        "Refund Policy finance Submit receipts within 30 days."
    )


def test_keyword_retrieval_uses_cached_document_terms() -> None:
    tokenizer = FakeTokenizer()
    strategy = KeywordRetrievalStrategy(tokenizer)
    documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
        Document(id="2", title="Vacation Policy", category="hr", text="Two week notice"),
    ]

    first_results = strategy.retrieve("refund policy", documents, limit=1)
    second_results = strategy.retrieve("refund policy", documents, limit=1)

    assert [document.id for document in first_results] == ["1"]
    assert [document.id for document in second_results] == ["1"]
    assert tokenizer.calls.count("Refund Policy finance Receipts required") == 1
    assert tokenizer.calls.count("Vacation Policy hr Two week notice") == 1


def test_keyword_retrieval_refreshes_cache_when_document_text_changes() -> None:
    tokenizer = FakeTokenizer()
    strategy = KeywordRetrievalStrategy(tokenizer)
    original_documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
    ]
    updated_documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Director approval required"),
    ]

    strategy.retrieve("refund", original_documents, limit=1)
    strategy.retrieve("director", updated_documents, limit=1)

    assert "Refund Policy finance Receipts required" in tokenizer.calls
    assert "Refund Policy finance Director approval required" in tokenizer.calls


def test_embedding_retrieval_indexes_shared_document_text(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    strategy = EmbeddingRetrievalStrategy("fake-model")
    documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
        Document(id="2", title="Vacation Guide", category="hr", text="Two week notice"),
    ]

    strategy.build_index(documents)

    assert strategy.model.calls[0] == [
        "Refund Policy finance Receipts required",
        "Vacation Guide hr Two week notice",
    ]


def test_embedding_retrieval_resets_index_on_rebuild(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    strategy = EmbeddingRetrievalStrategy("fake-model")
    original_documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
    ]
    replacement_documents = [
        Document(id="2", title="Vacation Guide", category="hr", text="Two week notice"),
    ]

    strategy.build_index(original_documents)
    strategy.build_index(replacement_documents)
    results = strategy.retrieve("vacation request", replacement_documents, limit=1)

    assert strategy.index.ntotal == 1
    assert [document.id for document in results] == ["2"]


def test_embedding_retrieval_rebuilds_when_document_text_changes(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    strategy = EmbeddingRetrievalStrategy("fake-model")
    original_documents = [
        Document(id="1", title="Policy", category="ops", text="Refund workflow"),
    ]
    updated_documents = [
        Document(id="1", title="Policy", category="ops", text="Vacation workflow"),
    ]

    strategy.build_index(original_documents)
    results = strategy.retrieve("vacation request", updated_documents, limit=1)

    assert [document.id for document in results] == ["1"]
    assert strategy.model.calls[-2] == ["Policy ops Vacation workflow"]


def test_embedding_retrieval_returns_empty_for_low_similarity_queries(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    strategy = EmbeddingRetrievalStrategy("fake-model", min_similarity=0.8)
    documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
        Document(id="2", title="Vacation Guide", category="hr", text="Two week notice"),
    ]

    strategy.build_index(documents)
    results = strategy.retrieve("office badge hours", documents, limit=2)

    assert results == []
