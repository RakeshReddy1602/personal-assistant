from typing import List, Optional, Sequence, Dict
from textwrap import dedent

from agent.clients.gemini_client import generate
from agent.states.assistant_state import Message, AssistantState


class ResumeAgent:
    def __init__(self, model: str = "gemini-2.0-flash-lite") -> None:
        self.model = model

    def _format_history(self, history: Optional[Sequence[Message]]) -> str:
        if not history:
            return "(no prior messages)"
        lines = []
        for m in history:
            role = m.get("role", "user").capitalize()
            content = (m.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "(no prior messages)"

    def rewrite_summary(self, current_summary: str, target_role: str, history: Optional[Sequence[Message]] = None) -> str:
        history_block = self._format_history(history)
        prompt = dedent(
            f"""
            You are a professional resume writer. Rewrite the following resume summary
            to target the role: "{target_role}". Keep it concise (3-5 sentences),
            emphasize measurable impact, and avoid buzzwords.

            Chat history (most recent last):
            {history_block}

            Summary:
            {current_summary.strip()}

            Return only the rewritten summary.
            """
        ).strip()
        return generate(model=self.model, prompt=prompt).strip()

    def assist(self, instruction: str, history: Optional[Sequence[Message]] = None) -> str:
        history_block = self._format_history(history)
        prompt = dedent(
            f"""
            You are a professional resume assistant. Follow the user's instruction below to
            improve or produce resume content. Use the chat history only to disambiguate context.
            Do not invent experience. Prefer concise, high-impact phrasing and quantify where appropriate.

            Chat history (most recent last):
            {history_block}

            Instruction:
            {instruction.strip()}

            Return only the requested resume text or bullet points.
            """
        ).strip()
        return generate(model=self.model, prompt=prompt).strip()

    def bullets_from_experience(self, experience: str, role: str, history: Optional[Sequence[Message]] = None) -> List[str]:
        history_block = self._format_history(history)
        prompt = dedent(
            f"""
            Turn the following raw experience notes into 5-7 strong resume bullet points
            tailored for "{role}". Use action verbs, include metrics where sensible, and keep
            each bullet on one line.

            Chat history (most recent last):
            {history_block}

            Experience notes:
            {experience.strip()}

            Return only the bullet points, each on its own line, without numbering.
            """
        ).strip()
        text = generate(model=self.model, prompt=prompt)
        bullets = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
        return [b for b in bullets if b]

    def tailor_resume(self, resume_text: str, job_description: str, history: Optional[Sequence[Message]] = None) -> str:
        history_block = self._format_history(history)
        prompt = dedent(
            f"""
            You are tailoring a resume to a job description.
            - Keep the original structure but strengthen language and align keywords.
            - Do not invent experience. Prefer quantification where appropriate.
            - Keep total length approximately the same.

            Chat history (most recent last):
            {history_block}

            Job description:
            {job_description.strip()}

            Resume:
            {resume_text.strip()}

            Return the improved resume text only.
            """
        ).strip()
        return generate(model=self.model, prompt=prompt).strip()


def resume_handler(state: AssistantState) -> AssistantState:
    """
    LangGraph node handler for resume preparation. Uses ResumeAgent with history.
    """
    agent = ResumeAgent()
    query = (state.get("query_to_be_served") or "").strip()
    history = state.get("history") or []
    result = agent.assist(query, history=history) if query else ""
    state["response"] = result
    return state

