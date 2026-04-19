import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from dotenv import load_dotenv
from openai import AsyncOpenAI


RAW_DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Remote Work Policy",
        "category": "hr",
        "text": "Employees may work remotely up to three days per week with manager approval. Core collaboration hours are 10:00 to 15:00 local time. Security training must be completed before accessing internal systems from personal networks.",
    },
    {
        "id": "doc-002",
        "title": "Annual Leave Guidelines",
        "category": "hr",
        "text": "Full-time employees receive 18 days of annual leave each calendar year. Leave requests longer than five consecutive working days should be submitted at least two weeks in advance. Unused leave may be carried forward up to five days into the next year.",
    },
    {
        "id": "doc-003",
        "title": "Expense Reimbursement Rules",
        "category": "finance",
        "text": "Meals under 40 USD do not require pre-approval. Hotel bookings above 180 USD per night require director approval unless travel occurs during a peak event period. Expense claims must include receipts and be submitted within 30 days of purchase.",
    },
    {
        "id": "doc-004",
        "title": "Laptop Replacement Standard",
        "category": "it",
        "text": "Engineering laptops are eligible for replacement every 36 months. Early replacement is permitted for repeated hardware failures, battery health below 70 percent, or inability to run required local development tooling.",
    },
    {
        "id": "doc-005",
        "title": "Incident Severity Matrix",
        "category": "ops",
        "text": "A Sev-1 incident means customer-facing downtime affecting more than 50 percent of active users or any confirmed data loss event. Sev-2 covers major degradation with a workaround. Sev-3 covers minor feature impact without broad business disruption.",
    },
    {
        "id": "doc-006",
        "title": "Customer Support SLA",
        "category": "support",
        "text": "Priority enterprise tickets receive a first response within one hour during business hours. Standard tickets receive a first response within eight business hours. Bug reports linked to production outages are escalated immediately to engineering.",
    },
    {
        "id": "doc-007",
        "title": "Product Launch Checklist",
        "category": "product",
        "text": "Before launch, every feature must complete QA sign-off, documentation review, analytics event verification, and rollback plan approval. Features touching billing also require finance review and a staged release plan.",
    },
    {
        "id": "doc-008",
        "title": "Data Retention Policy",
        "category": "security",
        "text": "Application logs are retained for 90 days. Support chat transcripts are retained for 12 months. Deleted customer files remain in backup snapshots for up to 30 days before permanent removal.",
    },
    {
        "id": "doc-009",
        "title": "Engineering On-Call Expectations",
        "category": "engineering",
        "text": "Primary on-call engineers must acknowledge pager alerts within 10 minutes and begin triage within 15 minutes. If no acknowledgment occurs, the alert escalates automatically to the secondary on-call engineer and then to the engineering manager.",
    },
    {
        "id": "doc-010",
        "title": "Office Access Procedures",
        "category": "facilities",
        "text": "Employees may access the office from 07:00 to 22:00 using their badge. Guests must be registered by a host before arrival and remain escorted at all times outside reception and meeting rooms.",
    },
    {
        "id": "doc-011",
        "title": "Hiring Interview Rubric",
        "category": "recruiting",
        "text": "Interviewers score candidates across problem solving, communication, technical depth, and role alignment on a scale from 1 to 4. Written feedback should be submitted within 24 hours and must include at least two evidence-based observations.",
    },
    {
        "id": "doc-012",
        "title": "Vendor Review Requirements",
        "category": "procurement",
        "text": "New vendors handling customer data must complete a security questionnaire, sign a data processing agreement, and provide evidence of encryption at rest and in transit. Annual renewals require reassessment if risk exposure changes.",
    },
]


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str

    @classmethod
    def load(cls) -> "Settings":
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)

        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

        if not model:
            raise ValueError("OPENAI_MODEL is not set. Add it to your .env file.")

        return cls(api_key=api_key, model=model)


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    category: str
    text: str


class RetrievalStrategy(Protocol):
    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        """Return the most relevant documents for a query."""


class KeywordRetrievalStrategy:
    def retrieve(self, query: str, documents: list[Document], limit: int = 3) -> list[Document]:
        query_terms = self._tokenize(query)
        if not query_terms:
            return documents[:limit]

        scored_documents: list[tuple[int, Document]] = []
        for document in documents:
            searchable_text = " ".join((document.title, document.category, document.text))
            doc_terms = self._tokenize(searchable_text)
            overlap = len(query_terms & doc_terms)
            if overlap:
                scored_documents.append((overlap, document))

        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_documents[:limit]]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


class RAGChatbot:
    SYSTEM_PROMPT = (
        "You are a concise, helpful AI conversation partner for terminal chat practice. "
        "Use the retrieved context when it is relevant. If the answer is not supported by "
        "the context, say that clearly instead of inventing policy details."
    )

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        documents: Iterable[Document],
        retrieval_strategy: RetrievalStrategy,
    ) -> None:
        self.client = client
        self.model = model
        self.documents = list(documents)
        self.retrieval_strategy = retrieval_strategy

    def build_prompt(self, user_input: str, chat_history: list[tuple[str, str]]) -> str:
        prompt_sections = [self.SYSTEM_PROMPT]

        retrieved_documents = self.retrieval_strategy.retrieve(user_input, self.documents)
        if retrieved_documents:
            prompt_sections.append("Retrieved context:")
            for document in retrieved_documents:
                prompt_sections.append(
                    f"- [{document.id}] {document.title} ({document.category}): {document.text}"
                )

        if chat_history:
            prompt_sections.append("Conversation history:")
            for speaker, message in chat_history:
                prompt_sections.append(f"{speaker}: {message}")

        prompt_sections.append(f"User: {user_input}")
        prompt_sections.append("Assistant:")
        return "\n".join(prompt_sections)

    async def stream_chat_response(
        self, user_input: str, chat_history: list[tuple[str, str]] | None = None
    ):
        history = chat_history or []
        prompt = self.build_prompt(user_input, history)
        response = await self.client.responses.create(
            model=self.model,
            input=prompt,
            stream=True,
        )

        async for event in response:
            if event.type == "response.output_text.delta":
                yield event.delta


class TerminalChatApp:
    def __init__(self, chatbot: RAGChatbot) -> None:
        self.chatbot = chatbot
        self.chat_history: list[tuple[str, str]] = []

    async def run(self) -> None:
        print("AI: Hello! Type 'bye' to exit.")

        while True:
            try:
                user_text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAI: Goodbye!")
                break

            if not user_text:
                continue

            if user_text.lower() in {"bye", "exit", "quit"}:
                print("AI: Goodbye!")
                break

            response_chunks: list[str] = []
            print("AI: ", end="", flush=True)
            async for chunk in self.chatbot.stream_chat_response(user_text, self.chat_history):
                response_chunks.append(chunk)
                print(chunk, end="", flush=True)
            print()

            self.chat_history.append(("User", user_text))
            self.chat_history.append(("Assistant", "".join(response_chunks).strip()))


def build_documents() -> list[Document]:
    return [Document(**raw_document) for raw_document in RAW_DOCUMENTS]


def build_app() -> TerminalChatApp:
    settings = Settings.load()
    client = AsyncOpenAI(api_key=settings.api_key)
    retrieval_strategy = KeywordRetrievalStrategy()
    chatbot = RAGChatbot(
        client=client,
        model=settings.model,
        documents=build_documents(),
        retrieval_strategy=retrieval_strategy,
    )
    return TerminalChatApp(chatbot)


if __name__ == "__main__":
    asyncio.run(build_app().run())
