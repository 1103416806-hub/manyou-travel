from __future__ import annotations

from typing import Any

import httpx

from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class BrowserRetriever(BaseRetriever):
    source_type = "browser"

    async def retrieve(self, query: str, max_results: int = 5, **kwargs: Any) -> list[CandidateDoc]:
        search_url = f"https://www.google.com/search?q={query}"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, follow_redirects=True)
                resp.raise_for_status()
                html = resp.text
            except Exception:
                return []
        return [
            self._make_doc(
                doc_id=hashlib.md5(search_url.encode()).hexdigest()[:12],
                title=f"Browser search: {query}",
                snippet=html[:500],
                url=search_url,
                raw_content=html[:5000],
            )
        ]
