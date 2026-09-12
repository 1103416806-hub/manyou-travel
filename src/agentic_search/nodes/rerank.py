from __future__ import annotations

import logging

from agentic_search.rerank import cross_encoder_rerank, rrf_fuse
from agentic_search.state import CandidateDoc, SearchState

logger = logging.getLogger(__name__)


async def rerank_node(state: SearchState) -> dict:
    candidates = state.get("candidates", [])
    if not candidates:
        return {"ranked_docs": []}

    source_groups: dict[str, list[CandidateDoc]] = {}
    for doc in candidates:
        st = doc.get("source_type", "unknown")
        source_groups.setdefault(st, []).append(doc)

    rrf_results = rrf_fuse(source_groups)
    logger.info("Rerank: RRF produced %d docs from %d source groups", len(rrf_results), len(source_groups))

    query = state["query"]
    ranked = await cross_encoder_rerank(query, rrf_results)
    logger.info("Rerank: Cross-Encoder selected top %d docs", len(ranked))

    return {"ranked_docs": ranked}
