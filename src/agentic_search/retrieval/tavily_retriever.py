from __future__ import annotations

import hashlib
from typing import Any

import httpx
from langchain_tavily import TavilySearch

from agentic_search.config import settings
from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc


class TavilyRetriever(BaseRetriever):
    source_type = "tavily"

    def __init__(self) -> None:
        self._client = TavilySearch(
            max_results=10,
            tavily_api_key=settings.TAVILY_API_KEY,
        )

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        topic = kwargs.get("topic", "general")
        self._client.max_results = max_results
        self._client.topic = topic
        results = await self._client.ainvoke(query)
        docs: list[CandidateDoc] = []
        for r in results:
            url = r.get("url", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=r.get("title", ""),
                    snippet=r.get("content", ""),
                    url=url,
                    raw_content=r.get("raw_content", ""),
                    score=float(r.get("score", 0.0)),
                )
            )
        return docs


class BochaRetriever(BaseRetriever):
    source_type = "bocha"

    def __init__(self) -> None:
        self._api_key = settings.BOCHA_API_KEY
        self._base_url = "https://api.bochaai.com/v1/web-search"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        if not self._api_key:
            return []
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._base_url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"query": query, "count": max_results, "freshness": kwargs.get("freshness", "noLimit")},
            )
            resp.raise_for_status()
            data = resp.json()
        docs: list[CandidateDoc] = []
        for item in data.get("data", {}).get("webPages", {}).get("value", []):
            url = item.get("url", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=item.get("name", ""),
                    snippet=item.get("snippet", ""),
                    url=url,
                    raw_content=item.get("deepContent", ""),
                )
            )
        return docs
