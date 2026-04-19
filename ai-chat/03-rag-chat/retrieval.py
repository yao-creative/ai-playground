import tiktoken

from domain import Document, Tokenizer

from sentence_transformers import SentenceTransformer
import faiss


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

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:
            return documents[:limit]

        scored_documents: list[tuple[int, Document]] = []
        for document in documents:
            searchable_text = " ".join((document.title, document.category, document.text))
            doc_terms = self.tokenizer.tokenize(searchable_text)
            overlap = len(query_terms & doc_terms)
            if overlap:
                scored_documents.append((overlap, document))

        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_documents[:limit]]


class EmbeddingRetrievalStrategy:
    def __init__(self, model: str) -> None:
        self.model = SentenceTransformer(model)
        self.index = faiss.IndexFlatL2(self.model.get_embedding_dimension())
        self._has_index = False

    def build_index(self, documents: list[Document]) -> None:
        if not documents:
            self._has_index = False
            return

        embeddings = self.model.encode(
            [document.text for document in documents],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        self.index.add(embeddings)
        self._has_index = True

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        if not documents:
            return []

        if not self._has_index:
            self.build_index(documents)

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        _, indices = self.index.search(query_embedding, min(limit, len(documents)))
        return [documents[i] for i in indices[0] if i != -1]
