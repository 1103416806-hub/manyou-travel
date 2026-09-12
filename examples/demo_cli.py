"""
Interactive CLI demo for Agentic Search.
Requires ARK_API_KEY and at least one search API key configured.

Usage:
    python examples/demo_cli.py
"""
from __future__ import annotations

import asyncio
import uuid

from agentic_search.graph import compile_graph
from agentic_search.state import SearchState


async def interactive_search():
    print("🔍 Agentic Search — Interactive CLI")
    print("Type your query and press Enter. Type 'quit' to exit.\n")

    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    app = compile_graph(checkpointer=checkpointer)

    thread_id = str(uuid.uuid4())

    while True:
        query = input("🔎 Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not query:
            continue

        config = {"configurable": {"thread_id": thread_id}}

        initial_state: SearchState = {
            "query": query,
            "thread_id": thread_id,
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

        print("\n⏳ Searching...\n")

        try:
            result = await app.ainvoke(initial_state, config)
        except Exception as e:
            print(f"❌ Error: {e}\n")
            continue

        print("📝 Answer:")
        print("-" * 60)
        print(result.get("answer", "No answer generated"))
        print("-" * 60)

        citations = result.get("citations", [])
        if citations:
            print("\n📚 Citations:")
            for i, cit in enumerate(citations):
                print(f"  [{i}] {cit.get('title', 'Untitled')}")
                print(f"      {cit.get('url', 'No URL')}")
                print(f"      ({cit.get('source_type', 'unknown')})")

        confidence = result.get("confidence", 0.0)
        print(f"\n🎯 Confidence: {confidence:.2f}")
        print(f"🔄 Iterations: {result.get('iteration', 0)}\n")


if __name__ == "__main__":
    asyncio.run(interactive_search())
