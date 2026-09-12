from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agentic_search.config import settings
from agentic_search.graph import compile_graph


class SearchRequest(BaseModel):
    query: str
    thread_id: str | None = None


class SearchResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: float


app: FastAPI | None = None
compiled_graph = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    global compiled_graph
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.POSTGRES_DSN)
    await checkpointer.setup()
    compiled_graph = compile_graph(checkpointer=checkpointer)
    yield


def create_app() -> FastAPI:
    global app
    app = FastAPI(title="Agentic Search", version="0.1.0", lifespan=lifespan)
    _register_routes(app)
    return app


def _register_routes(fastapi_app: FastAPI) -> None:
    @fastapi_app.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "query": request.query,
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

        result = await compiled_graph.ainvoke(initial_state, config)

        return SearchResponse(
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
        )

    @fastapi_app.post("/search/stream")
    async def search_stream(request: SearchRequest) -> EventSourceResponse:
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "query": request.query,
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

        async def event_generator():
            async for event in compiled_graph.astream_events(initial_state, config, version="v2"):
                kind = event.get("event", "")
                name = event.get("name", "")
                data = event.get("data", {})

                if kind == "on_chain_end" and name in (
                    "supervisor",
                    "query",
                    "retrieval",
                    "rerank",
                    "reflection",
                    "synthesis",
                    "critic",
                ):
                    output = data.get("output", {})
                    yield {
                        "event": name,
                        "data": json.dumps(
                            {k: v for k, v in output.items() if k in ("plan", "intent", "sub_queries", "source_routing", "confidence", "decision", "answer", "citations", "critic_decision")},
                            ensure_ascii=False,
                            default=str,
                        ),
                    }

        return EventSourceResponse(event_generator())

    @fastapi_app.get("/health")
    async def health():
        return {"status": "ok"}
