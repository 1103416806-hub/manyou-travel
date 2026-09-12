from __future__ import annotations

from typing import Any

import httpx

from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class StructuredAPIRetriever(BaseRetriever):
    source_type = "structured_api"

    ENDPOINTS = {
        "stock": "https://api.example.com/stock",
        "weather": "https://api.example.com/weather",
        "exchange_rate": "https://api.example.com/exchange-rate",
    }

    async def retrieve(self, query: str, max_results: int = 5, **kwargs: Any) -> list[CandidateDoc]:
        api_type = kwargs.get("api_type")
        if not api_type or api_type not in self.ENDPOINTS:
            return []
        url = self.ENDPOINTS[api_type]
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params={"q": query}, timeout=10)
                resp.raise_for_status()
                content = resp.text
            except Exception:
                return []
        return [
            self._make_doc(
                doc_id=hashlib.md5(f"{api_type}:{query}".encode()).hexdigest()[:12],
                title=f"{api_type} data for: {query}",
                snippet=content[:500],
                url=url,
                raw_content=content,
            )
        ]
