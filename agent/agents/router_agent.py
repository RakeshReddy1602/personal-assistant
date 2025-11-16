from typing import Dict, Optional

from agent.states.assistant_state import AssistantState
from agent.constants import CATEGORIES, DEFAULT_ROUTER_MODEL
from agent.clients.ollama_client import generate_json
from agent.eval_queue import publish_eval_event


ROUTER_SYSTEM_PROMPT = (
    """
    You are a router. Classify the user's request into one category from the list.\n""" +

    "Categories: " + ", ".join(CATEGORIES) + "\n" +
    """Rules: 
    - You must be stricyly matching the user's request to the available categories only.
    - You must return the exact category that matches the user's request.
    - If the user's request is not related to any of the categories, return 'none'
    - You must return the category from specified list and just category name.
    """
)


def route_category(user_query: str) -> str:
    prompt = (
        ROUTER_SYSTEM_PROMPT
        + "User: "
        + user_query.strip()
        + "\nRespond with: {\"category\": \"<one_of_categories>\"}"
    )
    result: Optional[Dict] = generate_json(model=DEFAULT_ROUTER_MODEL, prompt=prompt)
    if result and "category" in result:
        return result["category"]
    return "none"


def get_assistant_state(user_query: str) -> AssistantState:
    category = route_category(user_query)
    return AssistantState(category_to_be_served=category)
 
 
def router_node(state: AssistantState) -> AssistantState:
    """
    LangGraph node: classify state's current query and set category_to_be_served.
    """
    import time
    start_time = time.time()
    
    query = state.get("query_to_be_served", "") or ""
    category = route_category(query)
    
    execution_time = (time.time() - start_time) * 1000
    
    # Publish eval event (async, non-blocking)
    publish_eval_event(
        agent_name="router_agent",
        query=f"Query: {query}",
        response=f"Category: {category}",
        category="router",
        metadata={
            "execution_time_ms": execution_time,
            "routed_category": category,
            "available_categories": CATEGORIES
        }
    )
    
    state["category_to_be_served"] = category
    return state