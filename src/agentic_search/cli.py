from __future__ import annotations

import asyncio
import click



@click.group()
def cli():
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, type=int, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    import uvicorn

    click.echo(f"🚀 Starting Agentic Search API on {host}:{port}")
    uvicorn.run(
        "agentic_search.api.server:create_app",
        host=host,
        port=port,
        factory=True,
        reload=reload,
    )


@cli.command()
@click.argument("query")
@click.option("--thread-id", default=None, help="Thread ID for multi-turn")
def search(query: str, thread_id: str | None):
    import uuid
    from langgraph.checkpoint.memory import MemorySaver
    from agentic_search.graph import compile_graph
    from agentic_search.state import SearchState

    tid = thread_id or str(uuid.uuid4())
    checkpointer = MemorySaver()
    app = compile_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": tid}}

    initial_state: SearchState = {
        "query": query,
        "thread_id": tid,
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

    click.echo(f"🔍 Searching: {query}\n")

    result = asyncio.run(app.ainvoke(initial_state, config))

    click.echo("📝 Answer:")
    click.echo("-" * 60)
    click.echo(result.get("answer", "No answer generated"))
    click.echo("-" * 60)

    citations = result.get("citations", [])
    if citations:
        click.echo("\n📚 Citations:")
        for i, cit in enumerate(citations):
            click.echo(f"  [{i}] {cit.get('title', 'Untitled')}")
            click.echo(f"      {cit.get('url', 'No URL')}")

    confidence = result.get("confidence", 0.0)
    click.echo(f"\n🎯 Confidence: {confidence:.2f}")


@cli.command()
def routes():
    from agentic_search.retrieval import get_available_routes

    click.echo("📋 Available retrieval routes:")
    for route in get_available_routes():
        click.echo(f"  - {route}")


def main():
    cli()


if __name__ == "__main__":
    main()
