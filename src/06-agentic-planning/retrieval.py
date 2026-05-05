from collections.abc import Sequence

import bm25s
import tiktoken

from domain import Document, Tokenizer



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

    def _tokenize_document(self, document: Document) -> set[str]:
        serialized_document = serialize_document_for_retrieval(document)
        cached_entry = self._document_terms.get(document.id)
        if cached_entry is not None and cached_entry[0] == serialized_document:
            return cached_entry[1]

        doc_terms = self.tokenizer.tokenize(serialized_document)
        self._document_terms[document.id] = (serialized_document, doc_terms)
        return doc_terms

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:
            return documents[:limit]

        scored_documents: list[tuple[int, Document]] = []
        for document in documents:
            overlap = len(query_terms & self._tokenize_document(document))
            if overlap:
                scored_documents.append((overlap, document))

        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_documents[:limit]]


class BM25RetrievalStrategy:
    def __init__(self, tokenizer: TiktokenTokenizer) -> None:
        self.tokenizer = tokenizer
        self._bm25_tokenizer = bm25s.tokenization.Tokenizer(
            lower=False,
            stopwords=[],
            splitter=self.tokenizer.tokenize_to_sequence,
        )
        self.retriever = bm25s.BM25()
        self._indexed_documents: list[tuple[str, str]] = []
        self._has_index = False

    def _serialize_documents(self, documents: Sequence[Document]) -> list[tuple[str, str]]:
        return [(document.id, serialize_document_for_retrieval(document)) for document in documents]

    def build_index(self, documents: list[Document]) -> None:
        self.retriever = bm25s.BM25()
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
