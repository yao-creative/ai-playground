import importlib.util
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
    BM25RetrievalStrategy,
    CrossEncoderReranker,
    EmbeddingRetrievalStrategy,
    HybridRetrievalStrategy,
    KeywordRetrievalStrategy,
    TiktokenTokenizer,
    serialize_document_for_retrieval,
)


def load_rag_main_module():
    spec = importlib.util.spec_from_file_location("rag_chat_main", RAG_CHAT_DIR / "main.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTokenizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def tokenize(self, text: str) -> set[str]:
        self.calls.append(text)
        return {token.lower() for token in text.split()}


class FakeSequenceTokenizer:
    def __init__(self) -> None:
        self.sequence_calls: list[str] = []

    def tokenize(self, text: str) -> set[str]:
        return set(self.tokenize_to_sequence(text))

    def tokenize_to_sequence(self, text: str) -> list[str]:
        self.sequence_calls.append(text)
        return [
            token.lower()
            for token in text.replace(".", "").replace(",", "").split()
            if token.strip()
        ]


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
            elif "vacation" in lower or "leave" in lower:
                vectors.append([0.0, 1.0])
            elif "office" in lower:
                vectors.append([0.7, 0.7])
            else:
                vectors.append([0.0, 0.0])

        array = np.asarray(vectors, dtype="float32")
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return array / norms


class FakeCrossEncoder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.calls: list[list[tuple[str, str]]] = []

    def predict(self, pairs):
        normalized_pairs = list(pairs)
        self.calls.append(normalized_pairs)

        scores = []
        for query, document in normalized_pairs:
            query_lower = query.lower()
            document_lower = document.lower()
            score = 0.0
            if "manager approval" in query_lower and "remote work policy" in document_lower:
                score = 0.95
            elif "refund" in query_lower and "refund policy" in document_lower:
                score = 0.95
            elif "vacation" in query_lower and "vacation guide" in document_lower:
                score = 0.9
            elif "office" in query_lower and "office hours" in document_lower:
                score = 0.85
            elif "manager approval" in document_lower:
                score = 0.8
            scores.append(score)

        return np.asarray(scores, dtype="float32")


class RaisingCrossEncoder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def predict(self, pairs):
        raise RuntimeError("reranker unavailable")


def test_settings_loads_reranker_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.setenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")

    settings = Settings.load()

    assert settings.chat_model == "gpt-5-mini"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.reranker_model == "cross-encoder/ms-marco-MiniLM-L6-v2"


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


def test_tiktoken_tokenizer_returns_bm25_sequence_tokens() -> None:
    tokenizer = TiktokenTokenizer("gpt-4o-mini")

    tokens = tokenizer.tokenize_to_sequence("Remote work, remote WORK policy.")

    assert "remote" in tokens
    assert "work" in tokens
    assert tokens.count("remote") == 2


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


def test_bm25_retrieval_indexes_shared_document_text() -> None:
    tokenizer = FakeSequenceTokenizer()
    strategy = BM25RetrievalStrategy(tokenizer)
    documents = [
        Document(id="1", title="Refund Policy", category="finance", text="Receipts required"),
        Document(id="2", title="Vacation Guide", category="hr", text="Two week notice"),
    ]

    strategy.build_index(documents)

    assert strategy._indexed_documents == [
        ("1", "Refund Policy finance Receipts required"),
        ("2", "Vacation Guide hr Two week notice"),
    ]
    assert tokenizer.sequence_calls[:2] == [
        "Refund Policy finance Receipts required",
        "Vacation Guide hr Two week notice",
    ]


def test_bm25_retrieval_rebuilds_when_document_text_changes() -> None:
    tokenizer = FakeSequenceTokenizer()
    strategy = BM25RetrievalStrategy(tokenizer)
    original_documents = [
        Document(id="1", title="Policy", category="ops", text="Refund workflow"),
    ]
    updated_documents = [
        Document(id="1", title="Policy", category="ops", text="Vacation workflow"),
    ]

    strategy.build_index(original_documents)
    results = strategy.retrieve("vacation", updated_documents, limit=1)

    assert [document.id for document in results] == ["1"]
    assert "Policy ops Vacation workflow" in tokenizer.sequence_calls


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


def test_hybrid_retrieval_merges_candidates_without_duplicates(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setattr("retrieval.CrossEncoder", FakeCrossEncoder)
    documents = [
        Document(id="1", title="Remote Work Policy", category="hr", text="Manager approval required"),
        Document(id="2", title="Vacation Guide", category="hr", text="Annual leave process"),
        Document(id="3", title="Office Hours", category="facilities", text="Badge access 07:00 to 22:00"),
    ]

    lexical_strategy = BM25RetrievalStrategy(FakeSequenceTokenizer())
    lexical_strategy.build_index(documents)
    embedding_strategy = EmbeddingRetrievalStrategy("fake-model")
    embedding_strategy.build_index(documents)
    reranker = CrossEncoderReranker("fake-cross-encoder")
    strategy = HybridRetrievalStrategy(
        lexical_strategy=lexical_strategy,
        embedding_strategy=embedding_strategy,
        reranker=reranker,
    )

    results = strategy.retrieve("manager approval for remote work", documents, limit=3)

    assert results[0].id == "1"
    assert {document.id for document in results} == {"1", "2", "3"}
    assert len({document.id for document in results}) == 3


def test_hybrid_retrieval_reranks_fused_candidates_with_cross_encoder(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setattr("retrieval.CrossEncoder", FakeCrossEncoder)
    documents = [
        Document(id="1", title="Vacation Guide", category="hr", text="Leave requests"),
        Document(id="2", title="Refund Policy", category="finance", text="Receipts within 30 days"),
    ]

    lexical_strategy = BM25RetrievalStrategy(FakeSequenceTokenizer())
    lexical_strategy.build_index(documents)
    embedding_strategy = EmbeddingRetrievalStrategy("fake-model")
    embedding_strategy.build_index(documents)
    reranker = CrossEncoderReranker("fake-cross-encoder")
    strategy = HybridRetrievalStrategy(
        lexical_strategy=lexical_strategy,
        embedding_strategy=embedding_strategy,
        reranker=reranker,
    )

    results = strategy.retrieve("refund request", documents, limit=2)

    assert [document.id for document in results] == ["2", "1"]
    assert reranker.model.calls


def test_hybrid_retrieval_falls_back_to_fused_order_when_reranker_raises(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setattr("retrieval.CrossEncoder", RaisingCrossEncoder)
    documents = [
        Document(id="1", title="Remote Work Policy", category="hr", text="Manager approval required"),
        Document(id="2", title="Vacation Guide", category="hr", text="Annual leave process"),
    ]

    lexical_strategy = BM25RetrievalStrategy(FakeSequenceTokenizer())
    lexical_strategy.build_index(documents)
    embedding_strategy = EmbeddingRetrievalStrategy("fake-model")
    embedding_strategy.build_index(documents)
    reranker = CrossEncoderReranker("broken-cross-encoder")
    strategy = HybridRetrievalStrategy(
        lexical_strategy=lexical_strategy,
        embedding_strategy=embedding_strategy,
        reranker=reranker,
    )

    results = strategy.retrieve("manager approval for remote work", documents, limit=2)

    assert [document.id for document in results] == ["1", "2"]


def test_build_app_supports_bm25_and_hybrid(monkeypatch) -> None:
    rag_main = load_rag_main_module()

    monkeypatch.setattr(
        rag_main.Settings,
        "load",
        classmethod(
            lambda cls: Settings(
                api_key="test-key",
                chat_model="gpt-5-mini",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                reranker_model="cross-encoder/ms-marco-MiniLM-L6-v2",
            )
        ),
    )
    monkeypatch.setattr(rag_main, "AsyncOpenAI", lambda **kwargs: object())

    class FakeBM25Strategy:
        def __init__(self, tokenizer) -> None:
            self.tokenizer = tokenizer
            self.build_index_calls = []

        def build_index(self, documents) -> None:
            self.build_index_calls.append(list(documents))

        def retrieve(self, query, documents, limit=3):
            return []

    class FakeEmbeddingStrategy:
        def __init__(self, model_name) -> None:
            self.model_name = model_name
            self.build_index_calls = []

        def build_index(self, documents) -> None:
            self.build_index_calls.append(list(documents))

        def retrieve(self, query, documents, limit=3):
            return []

    class FakeReranker:
        def __init__(self, model_name) -> None:
            self.model_name = model_name

    class FakeHybridStrategy:
        def __init__(self, lexical_strategy, embedding_strategy, reranker) -> None:
            self.lexical_strategy = lexical_strategy
            self.embedding_strategy = embedding_strategy
            self.reranker = reranker

        def retrieve(self, query, documents, limit=3):
            return []

    monkeypatch.setattr(rag_main, "BM25RetrievalStrategy", FakeBM25Strategy)
    monkeypatch.setattr(rag_main, "EmbeddingRetrievalStrategy", FakeEmbeddingStrategy)
    monkeypatch.setattr(rag_main, "CrossEncoderReranker", FakeReranker)
    monkeypatch.setattr(rag_main, "HybridRetrievalStrategy", FakeHybridStrategy)

    bm25_app = rag_main.build_app(strategy="bm25")
    hybrid_app = rag_main.build_app(strategy="hybrid")

    assert bm25_app.chatbot.retrieval_strategy.build_index_calls
    assert isinstance(hybrid_app.chatbot.retrieval_strategy.lexical_strategy, FakeBM25Strategy)
    assert isinstance(hybrid_app.chatbot.retrieval_strategy.embedding_strategy, FakeEmbeddingStrategy)
    assert isinstance(hybrid_app.chatbot.retrieval_strategy.reranker, FakeReranker)
