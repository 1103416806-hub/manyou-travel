from __future__ import annotations

from typing import Any

import httpx
from qdrant_client import QdrantClient

from agentic_search.config import settings
from agentic_search.retrieval.base import BaseRetriever
from agentic_search.state import CandidateDoc
import hashlib


class QdrantRetriever(BaseRetriever):
    source_type = "qdrant"

    def __init__(self) -> None:
        self._client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
        self._collection = settings.QDRANT_COLLECTION

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        try:
            from volcenginesdkarkruntime import Ark

            client = Ark(api_key=settings.ARK_API_KEY, base_url=settings.ARK_BASE_URL)
            resp = client.embeddings.create(model=kwargs.get("embedding_model", "bge-m3"), input=query)
            query_vector = resp.data[0].embedding
        except Exception:
            return []
        results = self._client.search(collection_name=self._collection, query_vector=query_vector, limit=max_results)
        docs: list[CandidateDoc] = []
        for hit in results:
            payload = hit.payload or {}
            url = payload.get("url", "")
            docs.append(
                self._make_doc(
                    doc_id=str(hit.id),
                    title=payload.get("title", ""),
                    snippet=payload.get("text", "")[:500],
                    url=url,
                    raw_content=payload.get("text", ""),
                    score=hit.score,
                )
            )
        return docs


class FeishuWikiRetriever(BaseRetriever):
    source_type = "feishu_wiki"

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
            return []
        token = await self._get_tenant_token()
        if not token:
            return []
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/search/v2/article",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"search_key": query, "page_size": max_results},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []
        docs: list[CandidateDoc] = []
        for item in data.get("data", {}).get("items", []):
            url = item.get("url", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=url,
                    raw_content=item.get("snippet", ""),
                )
            )
        return docs

    async def _get_tenant_token(self) -> str:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={"app_id": settings.FEISHU_APP_ID, "app_secret": settings.FEISHU_APP_SECRET},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json().get("tenant_access_token", "")
            except Exception:
                return ""


class BM25Retriever(BaseRetriever):
    source_type = "bm25"

    def __init__(self) -> None:
        self._corpus: list[str] = []
        self._metadata: list[dict] = []

    def add_documents(self, documents: list[dict]) -> None:
        for doc in documents:
            self._corpus.append(doc.get("text", ""))
            self._metadata.append(doc)

    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        if not self._corpus:
            return []
        from rank_bm25 import BM25Okapi

        tokenized_corpus = [doc.split() for doc in self._corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.split()
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:max_results]
        docs: list[CandidateDoc] = []
        for idx in top_indices:
            meta = self._metadata[idx]
            url = meta.get("url", "")
            docs.append(
                self._make_doc(
                    doc_id=hashlib.md5(f"bm25:{idx}:{url}".encode()).hexdigest()[:12],
                    title=meta.get("title", ""),
                    snippet=self._corpus[idx][:500],
                    url=url,
                    raw_content=self._corpus[idx],
                    score=float(scores[idx]),
                )
            )
        return docs
