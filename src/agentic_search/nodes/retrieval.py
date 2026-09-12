from __future__ import annotations

import asyncio
import logging

from agentic_search.config import settings
from agentic_search.retrieval import get_retrievers_for_route
from agentic_search.state import CandidateDoc, SearchState

logger = logging.getLogger(__name__)


def _deduplicate(docs: list[CandidateDoc]) -> list[CandidateDoc]:
    seen: set[str] = set()
    result: list[CandidateDoc] = []
    for doc in docs:
        key = doc.get("url") or doc["doc_id"]
        if key not in seen:
            seen.add(key)
            result.append(doc)
    return result


async def _retrieve_from_source(
    retrievers: list,
    queries: list[str],
    max_per_query: int = 10,
) -> list[CandidateDoc]:
    all_docs: list[CandidateDoc] = []
    for retriever in retrievers:
        for query in queries:
            try:
                docs = await retriever.retrieve(query, max_results=max_per_query)
                all_docs.extend(docs)
            except Exception:
                continue
    return all_docs


async def retrieval_node(state: SearchState) -> dict:
    source_routing = state.get("source_routing", ["timeliness", "fallback"])
    sub_queries = state.get("sub_queries", [state["query"]])
    max_per_query = max(5, settings.CANDIDATE_POOL_MAX // (len(sub_queries) * len(source_routing) + 1))

    tasks = []
    route_keys = []
    for route in source_routing:
        retrievers = get_retrievers_for_route(route)
        if retrievers:
            tasks.append(_retrieve_from_source(retrievers, sub_queries, max_per_query))
            route_keys.append(route)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    source_results: dict[str, list[CandidateDoc]] = {}
    all_docs: list[CandidateDoc] = []
    for key, result in zip(route_keys, results):
        if isinstance(result, Exception):
            source_results[key] = []
            continue
        docs = _deduplicate(result)
        source_results[key] = docs
        all_docs.extend(docs)

    all_docs = _deduplicate(all_docs)[:settings.CANDIDATE_POOL_MAX]

    logger.info("Retrieval: %d candidates from %d routes", len(all_docs), len(route_keys))

    return {
        "candidates": all_docs,
    }
