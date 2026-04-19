from typing import Iterable

from openai import AsyncOpenAI

from domain import Document, RetrievalStrategy


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
