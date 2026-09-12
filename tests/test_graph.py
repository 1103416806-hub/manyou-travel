
from agentic_search.graph import build_graph


def test_graph_build():
    graph = build_graph()
    assert graph is not None
    nodes = list(graph.nodes.keys())
    expected_nodes = ["supervisor", "query", "retrieval", "rerank", "reflection", "synthesis", "critic"]
    for node in expected_nodes:
        assert node in nodes, f"Missing node: {node}"


def test_conditional_edges():
    from agentic_search.state import SearchState

    state: SearchState = {"query": "test", "decision": "end"}
    from agentic_search.graph import _should_end_after_supervisor

    assert _should_end_after_supervisor(state) == "end"
