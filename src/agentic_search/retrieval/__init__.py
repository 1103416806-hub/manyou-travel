from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_search.retrieval.base import BaseRetriever

_RETRIEVER_CLASSES: dict[str, list[str]] = {
    "timeliness": ["TavilyRetriever", "BochaRetriever"],
    "realtime": ["StructuredAPIRetriever"],
    "academic": ["ArxivRetriever", "SemanticScholarRetriever"],
    "code": ["GitHubRetriever", "StackOverflowRetriever"],
    "feedback": ["RedditRetriever", "XiaohongshuRetriever", "AppStoreRetriever"],
    "private": ["QdrantRetriever", "FeishuWikiRetriever", "BM25Retriever"],
    "fallback": ["BrowserRetriever"],
}

_MODULE_MAP: dict[str, str] = {
    "TavilyRetriever": "agentic_search.retrieval.tavily_retriever",
    "BochaRetriever": "agentic_search.retrieval.tavily_retriever",
    "StructuredAPIRetriever": "agentic_search.retrieval.structured_api",
    "ArxivRetriever": "agentic_search.retrieval.arxiv_retriever",
    "SemanticScholarRetriever": "agentic_search.retrieval.arxiv_retriever",
    "GitHubRetriever": "agentic_search.retrieval.code_retriever",
    "StackOverflowRetriever": "agentic_search.retrieval.code_retriever",
    "RedditRetriever": "agentic_search.retrieval.feedback_retriever",
    "XiaohongshuRetriever": "agentic_search.retrieval.feedback_retriever",
    "AppStoreRetriever": "agentic_search.retrieval.feedback_retriever",
    "QdrantRetriever": "agentic_search.retrieval.private_retriever",
    "FeishuWikiRetriever": "agentic_search.retrieval.private_retriever",
    "BM25Retriever": "agentic_search.retrieval.private_retriever",
    "BrowserRetriever": "agentic_search.retrieval.browser_retriever",
}

_cache: dict[str, "BaseRetriever"] = {}


def _get_retriever(name: str) -> "BaseRetriever":
    if name not in _cache:
        import importlib
        module = importlib.import_module(_MODULE_MAP[name])
        cls = getattr(module, name)
        _cache[name] = cls()
    return _cache[name]


def get_retrievers_for_route(route: str) -> list["BaseRetriever"]:
    class_names = _RETRIEVER_CLASSES.get(route, [])
    return [_get_retriever(name) for name in class_names]


def get_available_routes() -> list[str]:
    return list(_RETRIEVER_CLASSES.keys())


__all__ = ["get_retrievers_for_route", "get_available_routes"]
