from typing import List, Literal, TypedDict, Optional


class Message(TypedDict):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: Optional[str]  # Optional field for tool name


class AssistantState(TypedDict):
    category_to_be_served: str
    query_to_be_served: str
    history: List[Message]
    response: str