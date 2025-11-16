from typing import Any, Dict, Iterable, List, Optional, Sequence
from agent.states.assistant_state import AssistantState, Message

from agent.clients.ollama_client import generate_json
from agent.constants import DEFAULT_ROUTER_MODEL
from dotenv import load_dotenv
from agent.prompts.query_rewriter_prompts.prompt import QUERY_REWRITER_SYSTEM_PROMPT
from agent.eval_queue import publish_eval_event

load_dotenv()



def _normalize_history(messages: Optional[Iterable[str]]) -> List[str]:
    if not messages:
        return []
    return [str(m).strip() for m in messages if str(m).strip()]


def _format_history_for_prompt(history: Sequence[str]) -> str:
    if not history:
        return "(no prior messages)"
    return "\n".join([f"User: {content}" for content in history])


def build_rewrite_prompt(user_query: str, messages: Optional[Iterable[str]] = None) -> str:
    history_pairs = _normalize_history(messages)
    history_block = _format_history_for_prompt(history_pairs)
    prompt = (
        QUERY_REWRITER_SYSTEM_PROMPT
        + "\n\nChat history (most recent last):\n"
        + history_block
        + "\n\nUser: "
        + user_query.strip()
        + "\nRespond with: {\"rewritten_query\": \"<standalone_query>\"}"
    )
    print('--------------------------------')
    print(prompt)
    print('--------------------------------')
    return prompt


def rewrite_query(
    user_query: str,
    messages: Optional[Iterable[str]] = None,
    model: str = DEFAULT_ROUTER_MODEL,
) -> str:
    prompt = build_rewrite_prompt(user_query=user_query, messages=messages)
    result: Dict[str, Any] | None = generate_json(model=model, prompt=prompt)
    if isinstance(result, dict):
        rewritten = result.get("rewritten_query")
        if isinstance(rewritten, str) and rewritten.strip():
            return rewritten.strip()
    # Fallback to original query if model did not return parseable JSON
    return user_query.strip()


def rewrite_node(state: AssistantState) -> AssistantState:
    """
    LangGraph node: rewrite state's query using optional history.
    """
    import time
    start_time = time.time()
    
    history: List[Message] = state.get("history", []) or []  # type: ignore[assignment]
    history_texts = [m.get("content", "") for m in history if m.get("content")]
    
    original_query = state.get("query_to_be_served", "") or ""
    rewritten = rewrite_query(
        user_query=original_query,
        messages=history_texts,
    )
    
    execution_time = (time.time() - start_time) * 1000
    
    # Publish eval event (async, non-blocking)
    publish_eval_event(
        agent_name="query_rewriter",
        query=f"Original: {original_query}",
        response=f"Rewritten: {rewritten}",
        category="query_rewriter",
        metadata={
            "execution_time_ms": execution_time,
            "original_query": original_query,
            "rewritten_query": rewritten,
            "had_history": len(history_texts) > 0,
            "history_count": len(history_texts)
        }
    )
    
    state["query_to_be_served"] = rewritten
    print('--------------------------------')
    print(rewritten)
    print('--------------------------------')
    return state