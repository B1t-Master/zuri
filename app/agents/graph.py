"""LangGraph orchestration (Phase 4).

The graph will wire: SentimentAnalyser -> RouterAgent -> {QAAgent | EscalationManager}.

Placeholder for now so the FastAPI app boots and the structure is in place.
"""

from langgraph.graph import StateGraph


class AgentState(dict):
    """Full graph state lands in Phase 4."""

    pass


def build_graph():
    graph = StateGraph(AgentState)
    return graph.compile()