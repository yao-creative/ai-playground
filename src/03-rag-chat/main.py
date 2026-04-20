import asyncio
import argparse
from pathlib import Path
import sys

from openai import AsyncOpenAI

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.append(str(MODULE_DIR))

from chatbot import RAGChatbot
from config import Settings
from data import build_documents
from retrieval import (
    BM25RetrievalStrategy,
    CrossEncoderReranker,
    EmbeddingRetrievalStrategy,
    HybridRetrievalStrategy,
    KeywordRetrievalStrategy,
    TiktokenTokenizer,
)
from terminal_app import TerminalChatApp


def build_app(strategy: str = "keyword") -> TerminalChatApp:
    settings = Settings.load()
    client = AsyncOpenAI(api_key=settings.api_key)
    documents = build_documents()
    tokenizer = TiktokenTokenizer(settings.chat_model)

    if strategy == "embedding":
        retrieval_strategy = EmbeddingRetrievalStrategy(settings.embedding_model)
        retrieval_strategy.build_index(documents)
    elif strategy == "bm25":
        retrieval_strategy = BM25RetrievalStrategy(tokenizer)
        retrieval_strategy.build_index(documents)
    elif strategy == "hybrid":
        lexical_strategy = BM25RetrievalStrategy(tokenizer)
        lexical_strategy.build_index(documents)
        embedding_strategy = EmbeddingRetrievalStrategy(settings.embedding_model)
        embedding_strategy.build_index(documents)
        reranker = CrossEncoderReranker(settings.reranker_model)
        retrieval_strategy = HybridRetrievalStrategy(
            lexical_strategy=lexical_strategy,
            embedding_strategy=embedding_strategy,
            reranker=reranker,
        )
    else:
        retrieval_strategy = KeywordRetrievalStrategy(tokenizer)

    chatbot = RAGChatbot(
        client=client,
        model=settings.chat_model,
        documents=documents,
        retrieval_strategy=retrieval_strategy,
    )
    return TerminalChatApp(chatbot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Chatbot: terminal conversation app")
    parser.add_argument(
        "--strategy",
        choices=["keyword", "bm25", "embedding", "hybrid"],
        default="keyword",
        help=(
            "Retrieval strategy to use: 'keyword', 'bm25', 'embedding', "
            "or 'hybrid' (default: keyword)"
        ),
    )
    args = parser.parse_args()
    asyncio.run(build_app(strategy=args.strategy).run())
