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
from retrieval import KeywordRetrievalStrategy, TiktokenTokenizer, EmbeddingRetrievalStrategy
from terminal_app import TerminalChatApp


def build_app(strategy: str = "keyword") -> TerminalChatApp:
    settings = Settings.load()
    client = AsyncOpenAI(api_key=settings.api_key)
    documents = build_documents()
    if strategy == "embedding":
        retrieval_strategy = EmbeddingRetrievalStrategy(settings.embedding_model)
        retrieval_strategy.build_index(documents)
    else:
        tokenizer = TiktokenTokenizer(settings.chat_model)
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
        choices=["keyword", "embedding"],
        default="keyword",
        help="Retrieval strategy to use: 'keyword' or 'embedding' (default: keyword)"
    )
    args = parser.parse_args()
    asyncio.run(build_app(strategy=args.strategy).run())
