import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CHAT_DIR = REPO_ROOT / "ai-chat"
RAG_CHAT_DIR = AI_CHAT_DIR / "03-rag-chat"

for path in (AI_CHAT_DIR, RAG_CHAT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from config import Settings
from domain import Document
from retrieval import EmbeddingRetrievalStrategy


class FakeSentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

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

        vectors = []
        for text in inputs:
            lower = text.lower()
            if "refund" in lower:
                vectors.append([1.0, 0.0])
            elif "vacation" in lower:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return __import__("numpy").asarray(vectors, dtype="float32")


def test_settings_uses_separate_chat_and_embedding_models(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    settings = Settings.load()

    assert settings.chat_model == "gpt-5-mini"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_embedding_retrieval_returns_nearest_documents(monkeypatch) -> None:
    monkeypatch.setattr(
        "retrieval.SentenceTransformer",
        FakeSentenceTransformer,
    )
    strategy = EmbeddingRetrievalStrategy("fake-model")
    documents = [
        Document(id="1", title="Refunds", category="policy", text="Refund policy details"),
        Document(id="2", title="Vacation", category="policy", text="Vacation policy details"),
    ]

    strategy.build_index(documents)
    results = strategy.retrieve("How do refunds work?", documents, limit=1)

    assert [document.id for document in results] == ["1"]
