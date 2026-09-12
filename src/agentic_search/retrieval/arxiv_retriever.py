from __future__ import annotations

from typing import Any

import arxiv

from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class ArxivRetriever(BaseRetriever):
    source_type = "arxiv"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        docs: list[CandidateDoc] = []
        for result in client.results(search):
            url = result.entry_id
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=result.title,
                    snippet=result.summary[:500],
                    url=url,
                    raw_content=result.summary,
                )
            )
        return docs


class SemanticScholarRetriever(BaseRetriever):
    source_type = "semantic_scholar"

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        import httpx

        params = {"query": query, "limit": max_results, "fields": "title,url,abstract,year,citationCount"}
        headers = {}
        api_key = kwargs.get("api_key", "")
        if api_key:
            headers["x-api-key"] = api_key
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.BASE_URL, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for paper in data.get("data", []):
            url = paper.get("url", "")
            abstract = paper.get("abstract", "") or ""
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=paper.get("title", ""),
                    snippet=abstract[:500],
                    url=url,
                    raw_content=abstract,
                )
            )
        return docs
