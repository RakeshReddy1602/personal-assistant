import argparse
import json
from typing import Dict

from agent.states.assistant_state import AssistantState
from agent.constants import CATEGORIES, DEFAULT_ROUTER_MODEL
from agent.clients.ollama_client import generate_json


ROUTER_SYSTEM_PROMPT = (
    """
    You are a router. Classify the user's request into one category from the list.\n""" +

    "Categories: " + ", ".join(CATEGORIES) + "\n" +
    """Rules: 
    - You must be stricyly matching the user's request to the available categories only.
    - You must return the exact category that matches the user's request.
    - If the user's request is not related to any of the categories, return 'none'.
    - Return strict JSON with key 'category' only. No extra text.\n"
    """
)


def route_category(user_query: str) -> str:
    prompt = (
        ROUTER_SYSTEM_PROMPT
        + "User: "
        + user_query.strip()
        + "\nRespond with: {\"category\": \"<one_of_categories>\"}"
    )

    result: Dict | None = generate_json(model=DEFAULT_ROUTER_MODEL, prompt=prompt)
    category = (result or {}).get("category") if isinstance(result, dict) else None
    return category


def get_assistant_state(user_query: str) -> AssistantState:
    category = route_category(user_query)
    return AssistantState(category_to_be_served=category)
 
 
def router_node(state: AssistantState) -> AssistantState:
    """
    LangGraph node: classify state's current query and set category_to_be_served.
    """
    category = route_category(state.get("query_to_be_served", "") or "")
    state["category_to_be_served"] = category or "none"
    return state