from __future__ import annotations

from typing import Any

import httpx

from agentic_search.config import settings
from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class RedditRetriever(BaseRetriever):
    source_type = "reddit"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        headers = {"User-Agent": "AgenticSearch/0.1"}
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            token = await self._get_reddit_token()
            if token:
                headers["Authorization"] = f"bearer {token}"
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": max_results, "sort": "relevance"}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            permalink = f"https://www.reddit.com{post.get('permalink', '')}"
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(permalink.encode()).hexdigest()[:12],
                    title=post.get("title", ""),
                    snippet=post.get("selftext", "")[:500],
                    url=permalink,
                    raw_content=post.get("selftext", ""),
                )
            )
        return docs

    async def _get_reddit_token(self) -> str:
        import base64

        auth_str = f"{settings.REDDIT_CLIENT_ID}:{settings.REDDIT_CLIENT_SECRET}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
            "User-Agent": "AgenticSearch/0.1",
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    headers=headers,
                    data={"grant_type": "client_credentials"},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json().get("access_token", "")
            except Exception:
                return ""


class XiaohongshuRetriever(BaseRetriever):
    source_type = "xiaohongshu"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        return []


class AppStoreRetriever(BaseRetriever):
    source_type = "app_store"

    BASE_URL = "https://itunes.apple.com/search"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        params = {"term": query, "limit": max_results, "entity": "software"}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.BASE_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for app in data.get("results", []):
            url = app.get("trackViewUrl", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=app.get("trackName", ""),
                    snippet=app.get("description", "")[:500],
                    url=url,
                    raw_content=app.get("description", ""),
                )
            )
        return docs
