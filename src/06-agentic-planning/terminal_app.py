from orchestrator import AgenticPlanningOrchestrator
from models import AgentRunResult, PlanningSession


class TerminalChatApp:
    ACCEPT_PLAN_TOKENS = {"accept", "approve", "approved", "looks good", "proceed"}
    REDRAFT_PLAN_TOKENS = {"redraft", "revise", "edit plan"}
    EXIT_PLAN_TOKENS = {"exit plan", "cancel", "stop planning"}

    def __init__(self, chatbot: AgenticPlanningOrchestrator) -> None:
        self.chatbot = chatbot
        self.chat_history: list[tuple[str, str]] = []
        self.active_session: PlanningSession | None = None
        self.awaiting_redraft_feedback = False

    def run(self) -> None:
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

            response = self.handle_input(user_text)
            print(f"AI: {response}")

    def handle_input(self, user_text: str) -> str:
        if self.active_session is None:
            return self._start_plan_loop(user_text)
        return self._handle_plan_loop_input(user_text)

    def _start_plan_loop(self, user_text: str) -> str:
        prepared = self.chatbot.prepare_plan(user_text, self.chat_history)
        self.chat_history.append(("User", user_text))

        if isinstance(prepared, AgentRunResult):
            answer = self._format_answer(prepared)
            self.chat_history.append(("Assistant", answer))
            return answer

        self.active_session = prepared
        plan_text = self._format_plan(prepared)
        self.chat_history.append(("Assistant", plan_text))
        return plan_text

    def _handle_plan_loop_input(self, user_text: str) -> str:
        assert self.active_session is not None
        self.chat_history.append(("User", user_text))

        if self.awaiting_redraft_feedback:
            self.awaiting_redraft_feedback = False
            self.active_session = self.chatbot.redraft_plan(self.active_session, user_text)
            plan_text = self._format_plan(self.active_session)
            self.chat_history.append(("Assistant", plan_text))
            return plan_text

        if self._is_accept_intent(user_text):
            result = self.chatbot.execute_accepted_plan(self.active_session)
            self.active_session = None
            self.awaiting_redraft_feedback = False
            answer = self._format_answer(result)
            self.chat_history.append(("Assistant", answer))
            return answer

        if self._is_redraft_intent(user_text):
            message = "Redraft selected. Reply with the plan changes you want."
            self.chat_history.append(("Assistant", message))
            self.awaiting_redraft_feedback = True
            return message

        if self._is_exit_intent(user_text):
            self.active_session = None
            self.awaiting_redraft_feedback = False
            message = "Plan loop exited. No answer drafted for this turn."
            self.chat_history.append(("Assistant", message))
            return message

        message = "Choose one option: accept, redraft, or exit plan."
        self.chat_history.append(("Assistant", message))
        return message

    def _format_plan(self, session: PlanningSession) -> str:
        evidence_needed = session.plan.evidence_needed or ["None"]
        proposed_actions = session.plan.proposed_actions or ["None"]
        lines = [
            "Plan Spec:",
            f"Objective: {session.plan.objective}",
            "Evidence Needed:",
            *[f"- {item}" for item in evidence_needed],
            "Proposed Actions:",
            *[f"- {item}" for item in proposed_actions],
            "Options:",
            "- accept",
            "- redraft",
            "- exit plan",
        ]
        if session.revision_count > 0:
            lines.insert(1, f"Revision: {session.revision_count}")
        return "\n".join(lines)

    def _format_answer(self, result: AgentRunResult) -> str:
        answer = result.final_answer.strip()
        if result.supported and result.cited_doc_ids:
            return f"{answer}\nSources: {', '.join(result.cited_doc_ids)}"
        return answer

    def _is_accept_intent(self, user_text: str) -> bool:
        normalized = " ".join(user_text.lower().split())
        return normalized in self.ACCEPT_PLAN_TOKENS

    def _is_redraft_intent(self, user_text: str) -> bool:
        normalized = " ".join(user_text.lower().split())
        return normalized in self.REDRAFT_PLAN_TOKENS

    def _is_exit_intent(self, user_text: str) -> bool:
        normalized = " ".join(user_text.lower().split())
        return normalized in self.EXIT_PLAN_TOKENS

    @staticmethod
    def fallback_result() -> AgentRunResult:
        return AgentRunResult(
            final_answer="I do not have enough support in the docs to answer confidently.",
            cited_doc_ids=[],
            supported=False,
            steps=[],
        )
