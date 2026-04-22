from collections.abc import Sequence

import bm25s
import tiktoken

from domain import Document, RetrievedDoc, Retriever


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


class BM25Retriever(Retriever):
    def __init__(self, model: str) -> None:
        self.tokenizer = TiktokenTokenizer(model)
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

    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[RetrievedDoc]:
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
            return [
                RetrievedDoc(
                    id=document.id,
                    title=document.title,
                    category=document.category,
                    text=document.text,
                    rank=index + 1,
                    score=None,
                )
                for index, document in enumerate(documents[:limit])
            ]

        ids, scores = self.retriever.retrieve(
            query_tokens,
            corpus=np_ids(documents),
            k=min(limit, len(documents)),
            return_as="tuple",
            show_progress=False,
        )
        ranked_docs: list[RetrievedDoc] = []
        documents_by_id = {document.id: document for document in documents}
        for rank, (document_id, score) in enumerate(zip(ids[0], scores[0], strict=True), start=1):
            if document_id is None:
                continue
            document = documents_by_id[document_id]
            ranked_docs.append(
                RetrievedDoc(
                    id=document.id,
                    title=document.title,
                    category=document.category,
                    text=document.text,
                    rank=rank,
                    score=float(score),
                )
            )

        # Future seam: embeddings or rerankers can wrap this return value without changing main.py.
        return ranked_docs


def np_ids(documents: Sequence[Document]) -> list[str]:
    return [document.id for document in documents]
