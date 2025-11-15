from langgraph.graph import StateGraph, START, END
from agent.agents import query_rewriter
from agent.agents.resume_agent import resume_handler
from agent.states.assistant_state import AssistantState


def build_resume_subgraph():
    """
    Build a subgraph for resume preparation that includes:
    1. Query rewriter - to rewrite the query with history context
    2. Resume handler - to process the rewritten query
    """
    graph = StateGraph(AssistantState)
    
    # Add nodes
    graph.add_node('query_rewriter', query_rewriter.rewrite_node)
    graph.add_node('resume_handler', resume_handler)
    
    # Set entry point
    graph.set_entry_point('query_rewriter')
    graph.add_edge(START, 'query_rewriter')
    
    # Flow: query_rewriter -> resume_handler -> END
    graph.add_edge('query_rewriter', 'resume_handler')
    graph.add_edge('resume_handler', END)
    
    return graph.compile()

