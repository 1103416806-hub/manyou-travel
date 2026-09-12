from __future__ import annotations

from typing import Any

import httpx

from agentic_search.config import settings
from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class GitHubRetriever(BaseRetriever):
    source_type = "github"

    BASE_URL = "https://api.github.com/search/repositories"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        params = {"q": query, "per_page": max_results, "sort": "stars"}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.BASE_URL, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for repo in data.get("items", []):
            url = repo.get("html_url", "")
            desc = repo.get("description", "") or ""
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=repo.get("full_name", ""),
                    snippet=desc[:500],
                    url=url,
                    raw_content=desc,
                )
            )
        return docs


class StackOverflowRetriever(BaseRetriever):
    source_type = "stackoverflow"

    BASE_URL = "https://api.stackexchange.com/2.3/search/advanced"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        params = {"order": "desc", "sort": "relevance", "q": query, "site": "stackoverflow", "pagesize": max_results}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.BASE_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for item in data.get("items", []):
            url = item.get("link", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=item.get("title", ""),
                    snippet=item.get("title", ""),
                    url=url,
                    raw_content="",
                )
            )
        return docs
