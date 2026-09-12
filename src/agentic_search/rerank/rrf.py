from __future__ import annotations

from collections import defaultdict

from agentic_search.config import settings
from agentic_search.state import CandidateDoc


def rrf_fuse(
    source_results: dict[str, list[CandidateDoc]],
    k: int | None = None,
) -> list[CandidateDoc]:
    k = k or settings.RERANK_RRF_K
    rrf_scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, CandidateDoc] = {}

    for source_type, docs in source_results.items():
        for rank, doc in enumerate(docs, start=1):
            doc_id = doc["doc_id"]
            rrf_scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

    sorted_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)
    result: list[CandidateDoc] = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id].copy()
        doc["score"] = rrf_scores[doc_id]
        result.append(doc)
    return result
