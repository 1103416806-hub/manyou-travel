from __future__ import annotations

from typing import Any

import httpx

from agentic_search.config import settings
from agentic_search.state import CandidateDoc


async def cross_encoder_rerank(
    query: str,
    docs: list[CandidateDoc],
    top_k: int | None = None,
    top_n: int | None = None,
) -> list[CandidateDoc]:
    top_k = top_k or settings.RERANK_TOP_K
    top_n = top_n or settings.RERANK_CROSS_ENCODER_TOP_N

    candidates = docs[:top_n]
    if not candidates:
        return []

    documents = [d["snippet"] for d in candidates]
    payload: dict[str, Any] = {
        "model": "bge-reranker-v2-m3",
        "query": query,
        "documents": documents,
        "top_k": top_k,
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.RERANKER_API_KEY:
        headers["Authorization"] = f"Bearer {settings.RERANKER_API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                settings.RERANKER_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return candidates[:top_k]

    results: list[CandidateDoc] = []
    for item in data.get("results", []):
        idx = item.get("index", 0)
        score = item.get("relevance_score", 0.0)
        if idx < len(candidates):
            doc = candidates[idx].copy()
            doc["score"] = float(score)
            results.append(doc)

    results.sort(key=lambda d: d["score"], reverse=True)
    return results[:top_k]
