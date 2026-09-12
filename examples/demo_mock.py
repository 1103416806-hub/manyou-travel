"""
Mock demo: runs the full agentic search pipeline with simulated data.
No API keys required — all LLM calls and retrievers are mocked.

Usage:
    python examples/demo_mock.py
"""
from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

from agentic_search.state import SearchState


MOCK_DOCS = [
    {"doc_id": "d1", "title": "BGE Reranker v2 M3: A Multilingual Reranker",
     "snippet": "BGE-reranker-v2-m3 is a lightweight multilingual reranker model with 568M parameters, supporting 100+ languages.",
     "url": "https://huggingface.co/BAAI/bge-reranker-v2-m3", "source_type": "arxiv", "raw_content": "", "score": 0.0},
    {"doc_id": "d2", "title": "LangGraph: Building Multi-Agent Systems",
     "snippet": "LangGraph is a framework for building stateful, multi-actor applications with LLMs. It extends LangChain with cyclic graph support.",
     "url": "https://github.com/langchain-ai/langgraph", "source_type": "github", "raw_content": "", "score": 0.0},
    {"doc_id": "d3", "title": "RAG Fusion: Enhanced Retrieval via Multi-Query",
     "snippet": "RAG Fusion uses reciprocal rank fusion to combine results from multiple query variants, improving recall by 15-30%.",
     "url": "https://arxiv.org/abs/2402.02500", "source_type": "arxiv", "raw_content": "", "score": 0.0},
    {"doc_id": "d4", "title": "Self-RAG: Learning to Retrieve and Critique",
     "snippet": "Self-RAG introduces reflection tokens that allow the model to critique its own outputs, reducing hallucination by 40%.",
     "url": "https://arxiv.org/abs/2310.11511", "source_type": "arxiv", "raw_content": "", "score": 0.0},
    {"doc_id": "d5", "title": "Tavily Search API for AI Agents",
     "snippet": "Tavily provides a search API optimized for AI agents with built-in content extraction and relevance scoring.",
     "url": "https://tavily.com", "source_type": "tavily", "raw_content": "", "score": 0.0},
    {"doc_id": "d6", "title": "Qdrant: High-Performance Vector Database",
     "snippet": "Qdrant is an open-source vector similarity search engine supporting filtering, payload, and horizontal scaling.",
     "url": "https://qdrant.tech", "source_type": "qdrant", "raw_content": "", "score": 0.0},
    {"doc_id": "d7", "title": "Doubao: ByteDance's LLM Family",
     "snippet": "Doubao is ByteDance's large language model family available through the Volcengine Ark platform with OpenAI-compatible API.",
     "url": "https://www.volcengine.com/docs/82379", "source_type": "tavily", "raw_content": "", "score": 0.0},
    {"doc_id": "d8", "title": "Reciprocal Rank Fusion for Information Retrieval",
     "snippet": "RRF combines ranked lists from multiple sources using score(d) = sum(1/(k+rank_i(d))), achieving robust fusion without score normalization.",
     "url": "https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf", "source_type": "academic", "raw_content": "", "score": 0.0},
]


async def mock_llm_invoke(messages, **kwargs):
    class MockResponse:
        content = json.dumps({
            "plan": {"description": "Search for information about the query", "steps": ["Search web", "Search academic"], "focus_areas": ["general"]},
            "next_action": "query",
            "reasoning": "First iteration, need to search"
        })
    return MockResponse()


async def mock_supervisor_llm(messages, **kwargs):
    class MockResponse:
        content = json.dumps({
            "plan": {"description": "Search for information", "steps": ["Search"], "focus_areas": ["general"]},
            "next_action": "query",
            "reasoning": "Proceeding with search"
        })
    return MockResponse()


async def mock_query_llm(messages, **kwargs):
    class MockResponse:
        content = json.dumps({
            "intent": "academic",
            "sub_queries": ["bge-reranker-v2-m3 model", "multilingual reranker comparison", "BAAI reranker architecture"],
            "source_routing": ["academic", "timeliness"],
            "rewrite_strategy": "multi_query",
        })
    return MockResponse()


async def mock_reflection_llm(messages, **kwargs):
    class MockResponse:
        content = json.dumps({
            "relevance": 0.9,
            "sufficiency": 0.85,
            "consistency": 0.88,
            "gaps": [],
            "decision": "stop",
            "reasoning": "Evidence is sufficient to answer the query"
        })
    return MockResponse()


async def mock_synthesis_llm(messages, **kwargs):
    answer = """bge-reranker-v2-m3 is a lightweight multilingual reranker model developed by BAAI, featuring 568M parameters and supporting 100+ languages [0].

It is designed as a Cross-Encoder that takes (query, document) pairs as input and produces relevance scores, making it particularly effective for second-stage reranking in RAG pipelines [1].

The model can be used alongside Reciprocal Rank Fusion (RRF) in a two-stage reranking pipeline: RRF first fuses results from heterogeneous sources by rank position, then bge-reranker-v2-m3 performs semantic precision ranking on the top candidates [3][7].

Compared to other rerankers, it offers a strong balance between efficiency and accuracy, with multilingual support being a key differentiator [0]."""

    class MockResponse:
        content = json.dumps({
            "answer": answer,
            "citations": [
                {"source_id": "0", "url": "https://huggingface.co/BAAI/bge-reranker-v2-m3", "title": "BGE Reranker v2 M3", "snippet": "568M parameters, 100+ languages", "source_type": "arxiv"},
                {"source_id": "1", "url": "https://github.com/langchain-ai/langgraph", "title": "LangGraph", "snippet": "Multi-agent framework", "source_type": "github"},
                {"source_id": "3", "url": "https://arxiv.org/abs/2402.02500", "title": "RAG Fusion", "snippet": "Multi-query retrieval", "source_type": "arxiv"},
                {"source_id": "7", "url": "https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf", "title": "RRF for IR", "snippet": "Reciprocal Rank Fusion", "source_type": "academic"},
            ]
        })
    return MockResponse()


async def mock_critic_llm(messages, **kwargs):
    class MockResponse:
        content = json.dumps({
            "isRel": True,
            "isSup": True,
            "isUse": True,
            "ground": True,
            "details": "All citations verified, no hallucination detected",
            "decision": "pass"
        })
    return MockResponse()


async def mock_retriever_retrieve(self, query, max_results=10, **kwargs):
    return [doc.copy() for doc in MOCK_DOCS[:max_results]]


async def mock_retrieve_from_source(retrievers, queries, max_per_query=10):
    return [doc.copy() for doc in MOCK_DOCS[:max_per_query]]


async def mock_cross_encoder_rerank(query, docs, top_k=8, top_n=30):
    return docs[:top_k]


def print_step(step_name: str, data: dict):
    print(f"\n{'='*60}")
    print(f"  🔹 {step_name}")
    print(f"{'='*60}")
    for k, v in data.items():
        if isinstance(v, list) and len(v) > 3:
            print(f"  {k}: [{len(v)} items] {v[:2]}...")
        elif isinstance(v, dict):
            print(f"  {k}: {json.dumps(v, ensure_ascii=False, indent=2)}")
        else:
            print(f"  {k}: {v}")


async def run_mock_demo():
    print("🚀 Agentic Search — Mock Demo")
    print("📝 This demo uses simulated data. No API keys required.\n")

    from agentic_search.graph import build_graph

    graph = build_graph()
    app = graph.compile()

    initial_state: SearchState = {
        "query": "What is bge-reranker-v2-m3 and how does it compare to other rerankers?",
        "thread_id": str(uuid.uuid4()),
        "iteration": 0,
        "retry_count": 0,
        "sub_queries": [],
        "source_routing": [],
        "candidates": [],
        "ranked_docs": [],
        "gaps": [],
        "citations": [],
        "confidence": 0.0,
    }

    with patch("agentic_search.nodes.supervisor.get_llm_pro", return_value=AsyncMock(ainvoke=mock_supervisor_llm)), \
         patch("agentic_search.nodes.query.get_llm_lite", return_value=AsyncMock(ainvoke=mock_query_llm)), \
         patch("agentic_search.nodes.reflection.get_llm_lite", return_value=AsyncMock(ainvoke=mock_reflection_llm)), \
         patch("agentic_search.nodes.synthesis.get_llm_pro", return_value=AsyncMock(ainvoke=mock_synthesis_llm)), \
         patch("agentic_search.nodes.critic.get_llm_lite", return_value=AsyncMock(ainvoke=mock_critic_llm)), \
         patch("agentic_search.nodes.retrieval.get_retrievers_for_route", lambda route: []), \
         patch("agentic_search.nodes.retrieval._retrieve_from_source", mock_retrieve_from_source), \
         patch("agentic_search.rerank.cross_encoder.cross_encoder_rerank", mock_cross_encoder_rerank):

        print(f"Query: {initial_state['query']}\n")
        print("Running pipeline...\n")

        result = await app.ainvoke(initial_state)

    print_step("Final Result", {
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "confidence": result.get("confidence", 0.0),
        "iterations": result.get("iteration", 0),
    })

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(run_mock_demo())
