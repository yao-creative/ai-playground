import tiktoken

from domain import Document, Tokenizer

from sentence_transformers import SentenceTransformer
import faiss


def serialize_document_for_retrieval(document: Document) -> str:
    return " ".join((document.title, document.category, document.text))


class TiktokenTokenizer:
    def __init__(self, model: str) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("o200k_base")

    def tokenize(self, text: str) -> set[str]:
        token_ids = self.encoding.encode(text)
        normalized_tokens: set[str] = set()

        for token_id in token_ids:
            token = self.encoding.decode([token_id]).strip().lower()
            if not token:
                continue

            # Keep only tokens that carry word-like signal for lexical retrieval.
            compact = "".join(character for character in token if character.isalnum())
            if compact:
                normalized_tokens.add(compact)

        return normalized_tokens


class KeywordRetrievalStrategy:
    def __init__(self, tokenizer: Tokenizer) -> None:
        self.tokenizer = tokenizer
        self._document_terms: dict[str, tuple[str, set[str]]] = {}

    def _get_cached_document_terms(
        self, document_id: str, serialized_document: str
    ) -> set[str] | None:
        """Return cached terms only when the serialized document still matches."""
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


class EmbeddingRetrievalStrategy:
    def __init__(self, model: str, min_similarity: float = 0.3) -> None:
        self.model = SentenceTransformer(model)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        self._has_index = False
        self.min_similarity = min_similarity
        self._indexed_documents: list[tuple[str, str]] = []

    def build_index(self, documents: list[Document]) -> None:
        self.index = faiss.IndexFlatIP(self.dimension)
        self._indexed_documents = []

        if not documents:
            self._has_index = False
            return

        serialized_documents = [serialize_document_for_retrieval(document) for document in documents]
        embeddings = self.model.encode(
            serialized_documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        self.index.add(embeddings)
        self._indexed_documents = list(
            zip((document.id for document in documents), serialized_documents, strict=True)
        )
        self._has_index = True

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        if not documents:
            return []

        indexed_documents = [
            (document.id, serialize_document_for_retrieval(document)) for document in documents
        ]
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
