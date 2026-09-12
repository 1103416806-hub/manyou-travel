from __future__ import annotations

from langgraph.graph import END, StateGraph

from agentic_search.nodes import (
    critic_node,
    query_node,
    reflection_node,
    rerank_node,
    retrieval_node,
    supervisor_node,
    synthesis_node,
)
from agentic_search.state import SearchState


def _should_end_after_supervisor(state: SearchState) -> str:
    if state.get("decision") == "end":
        return "end"
    return "query"


def _route_after_reflection(state: SearchState) -> str:
    if state.get("decision") == "stop":
        return "synthesis"
    return "supervisor"


def _route_after_critic(state: SearchState) -> str:
    critic_decision = state.get("critic_decision", "pass")
    if critic_decision == "pass":
        return "end"
    if critic_decision == "hallucination":
        return "synthesis"
    return "supervisor"


def build_graph() -> StateGraph:
    graph = StateGraph(SearchState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("query", query_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        _should_end_after_supervisor,
        {"query": "query", "end": END},
    )

    graph.add_edge("query", "retrieval")
    graph.add_edge("retrieval", "rerank")
    graph.add_edge("rerank", "reflection")

    graph.add_conditional_edges(
        "reflection",
        _route_after_reflection,
        {"synthesis": "synthesis", "supervisor": "supervisor"},
    )

    graph.add_edge("synthesis", "critic")

    graph.add_conditional_edges(
        "critic",
        _route_after_critic,
        {"end": END, "synthesis": "synthesis", "supervisor": "supervisor"},
    )

    return graph


def compile_graph(checkpointer=None, store=None):
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer, store=store)
