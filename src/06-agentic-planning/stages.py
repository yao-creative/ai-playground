import json
from typing import Any

from models import DraftResult, PlanResult, ReviewResult


class StageJSONMixin:
    def _extract_json_object(self, response_text: str) -> dict[str, Any] | None:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = [line for line in cleaned.splitlines() if not line.startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                parsed = json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None

        return parsed if isinstance(parsed, dict) else None


class Planner(StageJSONMixin):
    def __init__(self, *, client, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, *, user_input: str, chat_history: list[tuple[str, str]], evidence_summary: str) -> PlanResult:
        prompt = "\n".join(
            [
                "You are a planning stage for a grounded assistant.",
                "Return JSON only with keys: objective, evidence_needed, proposed_actions.",
                "Keep each list short and concrete.",
                f"User question: {user_input}",
                f"Chat history: {chat_history[-6:]}",
                f"Evidence summary: {evidence_summary}",
            ]
        )
        response = self.client.responses.create(model=self.model, input=prompt, stream=False)
        payload = self._extract_json_object(str(getattr(response, "output_text", ""))) or {}

        objective = str(payload.get("objective", "Answer the user question with grounded evidence.")).strip()
        evidence_needed_raw = payload.get("evidence_needed", [])
        proposed_actions_raw = payload.get("proposed_actions", [])

        evidence_needed = [str(item) for item in evidence_needed_raw] if isinstance(evidence_needed_raw, list) else []
        proposed_actions = [str(item) for item in proposed_actions_raw] if isinstance(proposed_actions_raw, list) else []

        return PlanResult(
            objective=objective or "Answer the user question with grounded evidence.",
            evidence_needed=evidence_needed,
            proposed_actions=proposed_actions,
        )


class Drafter(StageJSONMixin):
    def __init__(self, *, client, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        *,
        user_input: str,
        plan: PlanResult,
        evidence_summary: str,
        chat_history: list[tuple[str, str]],
    ) -> DraftResult:
        prompt = "\n".join(
            [
                "You are a drafting stage for grounded QA.",
                "Return JSON only with keys: answer, cited_doc_ids, supported.",
                "Only cite doc ids that appear in evidence summary.",
                f"User question: {user_input}",
                f"Plan: {plan}",
                f"Chat history: {chat_history[-6:]}",
                f"Evidence summary: {evidence_summary}",
            ]
        )
        response = self.client.responses.create(model=self.model, input=prompt, stream=False)
        payload = self._extract_json_object(str(getattr(response, "output_text", ""))) or {}
        return self._coerce(payload)

    def _coerce(self, payload: dict[str, Any]) -> DraftResult:
        answer = str(payload.get("answer", "")).strip()
        cited_doc_ids_raw = payload.get("cited_doc_ids", [])
        cited_doc_ids = [str(doc_id) for doc_id in cited_doc_ids_raw] if isinstance(cited_doc_ids_raw, list) else []
        supported = bool(payload.get("supported", False))
        return DraftResult(
            answer=answer or "I do not have enough support in the docs to answer confidently.",
            cited_doc_ids=cited_doc_ids,
            supported=supported,
        )


class Reviewer(StageJSONMixin):
    def __init__(self, *, client, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, *, user_input: str, draft: DraftResult, evidence_summary: str) -> ReviewResult:
        prompt = "\n".join(
            [
                "You are a strict reviewer for grounded QA drafts.",
                "Return JSON only with keys: pass_review, issues, revision_instructions.",
                "Reject if claims are unsupported by evidence summary or citations are weak.",
                f"User question: {user_input}",
                f"Draft: {draft}",
                f"Evidence summary: {evidence_summary}",
            ]
        )
        response = self.client.responses.create(model=self.model, input=prompt, stream=False)
        payload = self._extract_json_object(str(getattr(response, "output_text", ""))) or {}
        pass_review = bool(payload.get("pass_review", False))
        issues_raw = payload.get("issues", [])
        issues = [str(issue) for issue in issues_raw] if isinstance(issues_raw, list) else []
        revision_instructions = str(payload.get("revision_instructions", "Improve grounding and citations.")).strip()
        return ReviewResult(
            pass_review=pass_review,
            issues=issues,
            revision_instructions=revision_instructions or "Improve grounding and citations.",
        )


class Redrafter(StageJSONMixin):
    def __init__(self, *, client, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        *,
        user_input: str,
        prior_draft: DraftResult,
        review: ReviewResult,
        evidence_summary: str,
    ) -> DraftResult:
        prompt = "\n".join(
            [
                "You are a redrafting stage for grounded QA.",
                "Return JSON only with keys: answer, cited_doc_ids, supported.",
                "Apply reviewer feedback precisely and do not invent new facts.",
                f"User question: {user_input}",
                f"Prior draft: {prior_draft}",
                f"Reviewer feedback: {review}",
                f"Evidence summary: {evidence_summary}",
            ]
        )
        response = self.client.responses.create(model=self.model, input=prompt, stream=False)
        payload = self._extract_json_object(str(getattr(response, "output_text", ""))) or {}

        answer = str(payload.get("answer", "")).strip()
        cited_doc_ids_raw = payload.get("cited_doc_ids", [])
        cited_doc_ids = [str(doc_id) for doc_id in cited_doc_ids_raw] if isinstance(cited_doc_ids_raw, list) else []
        supported = bool(payload.get("supported", False))
        return DraftResult(
            answer=answer or "I do not have enough support in the docs to answer confidently.",
            cited_doc_ids=cited_doc_ids,
            supported=supported,
        )
