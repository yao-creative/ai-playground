from openai import OpenAI

from domain import AnswerResult, RetrievedDoc, Usage


SYSTEM_PROMPT = (
    "You are a concise QA assistant for eval exercises. "
    "Answer only from the retrieved context. "
    "If the context does not support the answer, say that clearly."
)


def build_prompt(question: str, retrieved_docs: list[RetrievedDoc]) -> str:
    sections = [SYSTEM_PROMPT, "Retrieved context:"]

    if retrieved_docs:
        for document in retrieved_docs:
            sections.append(
                f"- [{document.id}] {document.title} ({document.category}): {document.text}"
            )
    else:
        sections.append("- No supporting documents were retrieved.")

    sections.append(f"Question: {question}")
    sections.append("Answer:")
    return "\n".join(sections)


class StubAnswerer:
    def __init__(self, model: str = "stub-answerer") -> None:
        self.model = model

    def answer(self, question: str, retrieved_docs: list[RetrievedDoc]) -> AnswerResult:
        prompt = build_prompt(question, retrieved_docs)
        if retrieved_docs:
            top_document = retrieved_docs[0]
            answer = (
                f"Stub mode: inspect [{top_document.id}] {top_document.title} and replace this "
                "with a real answerer or a judge-ready baseline."
            )
        else:
            answer = "Stub mode: no retrieved context. Replace this with refusal behavior exercises."

        return AnswerResult(
            answer=answer,
            prompt=prompt,
            model=self.model,
            usage=Usage(),
        )


class OpenAIAnswerer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def answer(self, question: str, retrieved_docs: list[RetrievedDoc]) -> AnswerResult:
        prompt = build_prompt(question, retrieved_docs)
        response = self.client.responses.create(model=self.model, input=prompt)
        usage = getattr(response, "usage", None)

        # Future seam: prompt templates, structured output, and provider-specific adapters belong here.
        return AnswerResult(
            answer=response.output_text.strip(),
            prompt=prompt,
            model=self.model,
            usage=Usage(
                input_tokens=getattr(usage, "input_tokens", None),
                output_tokens=getattr(usage, "output_tokens", None),
                total_tokens=getattr(usage, "total_tokens", None),
            ),
        )
