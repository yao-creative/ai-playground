from collections.abc import Sequence

import bm25s
import numpy as np
import tiktoken

from domain import Document, Tokenizer

SentenceTransformer = None
CrossEncoder = None
faiss = None


def _load_sentence_transformer() -> None:
    global SentenceTransformer
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as STSentenceTransformer

        SentenceTransformer = STSentenceTransformer


def _load_cross_encoder() -> None:
    global CrossEncoder
    if CrossEncoder is None:
        from sentence_transformers import CrossEncoder as STCrossEncoder

        CrossEncoder = STCrossEncoder


def _load_faiss() -> None:
    global faiss
    if faiss is None:
        import faiss as faiss_module

        faiss = faiss_module


def serialize_document_for_retrieval(document: Document) -> str:
    return " ".join((document.title, document.category, document.text))


class TiktokenTokenizer:
    def __init__(self, model: str) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("o200k_base")

    def tokenize_to_sequence(self, text: str) -> list[str]:
        token_ids = self.encoding.encode(text)
        normalized_tokens: list[str] = []

        for token_id in token_ids:
            token = self.encoding.decode([token_id]).strip().lower()
            if not token:
                continue

            compact = "".join(character for character in token if character.isalnum())
            if compact:
                normalized_tokens.append(compact)

        return normalized_tokens

    def tokenize(self, text: str) -> set[str]:
        return set(self.tokenize_to_sequence(text))


class KeywordRetrievalStrategy:
    def __init__(self, tokenizer: Tokenizer) -> None:
        self.tokenizer = tokenizer
        self._document_terms: dict[str, tuple[str, set[str]]] = {}

    def _get_cached_document_terms(
        self, document_id: str, serialized_document: str
    ) -> set[str] | None:
        cached_entry = self._document_terms.get(document_id)
        if cached_entry is not None and cached_entry[0] == serialized_document:
            return cached_entry[1]
        return None

    def _tokenize_document(self, document: Document) -> set[str]:
        serialized_document = serialize_document_for_retrieval(document)
        cached_terms = self._get_cached_document_terms(document.id, serialized_document)
        if cached_terms is not None:
            return cached_terms

        doc_terms = self.tokenizer.tokenize(serialized_document)
        self._document_terms[document.id] = (serialized_document, doc_terms)
        return doc_terms

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:
            return documents[:limit]

        scored_documents: list[tuple[int, Document]] = []
        for document in documents:
            doc_terms = self._tokenize_document(document)
            overlap = len(query_terms & doc_terms)
            if overlap:
                scored_documents.append((overlap, document))

        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_documents[:limit]]


class BM25RetrievalStrategy:
    def __init__(self, tokenizer: TiktokenTokenizer) -> None:
        self.tokenizer = tokenizer
        self._bm25_tokenizer = self._create_bm25_tokenizer()
        self.retriever = bm25s.BM25()
        self._indexed_documents: list[tuple[str, str]] = []
        self._has_index = False

    def _create_bm25_tokenizer(self):
        return bm25s.tokenization.Tokenizer(
            lower=False,
            stopwords=[],
            splitter=self.tokenizer.tokenize_to_sequence,
        )

    def _serialize_documents(self, documents: Sequence[Document]) -> list[tuple[str, str]]:
        return [(document.id, serialize_document_for_retrieval(document)) for document in documents]

    def build_index(self, documents: list[Document]) -> None:
        self.retriever = bm25s.BM25()
        self._bm25_tokenizer = self._create_bm25_tokenizer()
        self._indexed_documents = []

        if not documents:
            self._has_index = False
            return

        serialized_documents = [serialized for _, serialized in self._serialize_documents(documents)]
        tokenized_corpus = self._bm25_tokenizer.tokenize(
            serialized_documents,
            update_vocab="if_empty",
            show_progress=False,
        )
        self.retriever.index(tokenized_corpus, show_progress=False)
        self._indexed_documents = self._serialize_documents(documents)
        self._has_index = True

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        if not documents:
            return []

        indexed_documents = self._serialize_documents(documents)
        if not self._has_index or indexed_documents != self._indexed_documents:
            self.build_index(documents)

        query_tokens = self._bm25_tokenizer.tokenize(
            [query],
            update_vocab=False,
            show_progress=False,
        )
        if not query_tokens or not query_tokens[0]:
            return documents[:limit]

        results = self.retriever.retrieve(
            query_tokens,
            corpus=documents,
            k=min(limit, len(documents)),
            return_as="documents",
            show_progress=False,
        )
        return [document for document in results[0] if document is not None]


class EmbeddingRetrievalStrategy:
    def __init__(self, model: str, min_similarity: float = 0.3) -> None:
        _load_sentence_transformer()
        _load_faiss()

        self.model = SentenceTransformer(model)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        self._has_index = False
        self.min_similarity = min_similarity
        self._indexed_documents: list[tuple[str, str]] = []

    def _serialize_documents(self, documents: Sequence[Document]) -> list[tuple[str, str]]:
        return [(document.id, serialize_document_for_retrieval(document)) for document in documents]

    def build_index(self, documents: list[Document]) -> None:
        self.index = faiss.IndexFlatIP(self.dimension)
        self._indexed_documents = []

        if not documents:
            self._has_index = False
            return

        serialized_documents = [serialized for _, serialized in self._serialize_documents(documents)]
        embeddings = self.model.encode(
            serialized_documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        self.index.add(embeddings)
        self._indexed_documents = self._serialize_documents(documents)
        self._has_index = True

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        if not documents:
            return []

        indexed_documents = self._serialize_documents(documents)
        if not self._has_index or indexed_documents != self._indexed_documents:
            self.build_index(documents)

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        scores, indices = self.index.search(query_embedding, min(limit, len(documents)))

        results: list[Document] = []
        for score, index in zip(scores[0], indices[0], strict=True):
            if index == -1 or score < self.min_similarity:
                continue
            results.append(documents[index])

        return results


class CrossEncoderReranker:
    def __init__(self, model: str) -> None:
        _load_cross_encoder()
        self.model = CrossEncoder(model)

    def rerank(self, query: str, documents: Sequence[Document], limit: int) -> list[Document]:
        if not documents:
            return []

        pairs = [(query, serialize_document_for_retrieval(document)) for document in documents]
        scores = self.model.predict(pairs)
        ranked_pairs = sorted(
            zip(scores, documents, strict=True),
            key=lambda item: item[0],
            reverse=True,
        )
        return [document for _, document in ranked_pairs[:limit]]


class HybridRetrievalStrategy:
    def __init__(
        self,
        lexical_strategy: BM25RetrievalStrategy,
        embedding_strategy: EmbeddingRetrievalStrategy,
        reranker: CrossEncoderReranker,
    ) -> None:
        self.lexical_strategy = lexical_strategy
        self.embedding_strategy = embedding_strategy
        self.reranker = reranker

    def _candidate_limit(self, limit: int, document_count: int) -> int:
        return min(document_count, max(limit * 2, 6))

    def _fuse_ranked_documents(
        self,
        rankings: Sequence[Sequence[Document]],
    ) -> list[Document]:
        fused_scores: dict[str, float] = {}
        documents_by_id: dict[str, Document] = {}

        for ranking in rankings:
            for rank, document in enumerate(ranking, start=1):
                documents_by_id.setdefault(document.id, document)
                fused_scores[document.id] = fused_scores.get(document.id, 0.0) + 1.0 / (60 + rank)

        ranked_ids = sorted(
            fused_scores,
            key=lambda document_id: fused_scores[document_id],
            reverse=True,
        )
        return [documents_by_id[document_id] for document_id in ranked_ids]

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        if not documents:
            return []

        candidate_limit = self._candidate_limit(limit, len(documents))
        lexical_results = self.lexical_strategy.retrieve(query, documents, limit=candidate_limit)
        embedding_results = self.embedding_strategy.retrieve(query, documents, limit=candidate_limit)
        fused_results = self._fuse_ranked_documents((lexical_results, embedding_results))

        if not fused_results:
            return []

        try:
            return self.reranker.rerank(query, fused_results, limit=limit)
        except Exception:
            return fused_results[:limit]
