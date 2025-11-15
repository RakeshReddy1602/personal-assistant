from langgraph.graph import StateGraph, START, END
from agent.agents import query_rewriter, router_agent
from agent.states.assistant_state import AssistantState
from agent.agents.master import handle_master
from agent.schema.init_resume_agent_graph import build_resume_subgraph


def init_assistant_graph():
    return StateGraph(AssistantState)


# Conditional routing based on category
def _route_decider(state: AssistantState) -> str:
    category = (state.get("category_to_be_served") or "").strip().lower()
    if category in {"mail", "calendar", "drive", "expense_tracker"}:
        return 'master'
    if category in {"resume_preparation", "resume_prep", "resume"}:
        return 'resume'
    return 'none'


def no_category_handler(state: AssistantState) -> AssistantState:
    state["response"] = """I'm sorry, I am not capable of handling this request.
I can handle the following categories:
- Mails
- Calendar
- Expense Tracker
- Resume Preparation
"""
    return state


def build_graph():
    """
    Build the main assistant graph with:
    - Query rewriter (for master agent queries)
    - Router (categorizes the query)
    - Master agent (handles mail, calendar, etc.)
    - Resume subgraph (handles resume preparation with its own query rewriter)
    - None handler (for unsupported categories)
    """
    graph = StateGraph(AssistantState)
    
    # Add nodes
    graph.add_node('query_rewriter', query_rewriter.rewrite_node)
    graph.add_node('router', router_agent.router_node)
    graph.add_node('master', handle_master)
    graph.add_node('none', no_category_handler)
    
    # Add resume subgraph as a node
    resume_subgraph = build_resume_subgraph()
    graph.add_node('resume', resume_subgraph)
    
    # Set entry point and flow
    # graph.set_entry_point('query_rewriter')
    # graph.add_edge(START, 'query_rewriter')
    # graph.add_edge('query_rewriter', 'router')

    graph.set_entry_point('query_rewriter')
    graph.add_edge(START, 'query_rewriter')
    graph.add_edge('query_rewriter', 'router')
    
    # Conditional routing from router
    graph.add_conditional_edges(
        'router',
        _route_decider,
        {
            'master': 'master',
            'resume': 'resume',
            'none': 'none'
        }
    )
    
    # All paths lead to END
    graph.add_edge('master', END)
    graph.add_edge('resume', END)
    graph.add_edge('none', END)
    
    return graph.compile()

