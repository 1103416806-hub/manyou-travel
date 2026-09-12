import pytest
from unittest.mock import AsyncMock, patch

from agentic_search.retrieval.base import BaseRetriever
from agentic_search.retrieval.browser_retriever import BrowserRetriever


class ConcreteRetriever(BaseRetriever):
    source_type = "test"

    async def retrieve(self, query, max_results=10, **kwargs):
        return []


class TestBaseRetriever:
    def test_make_doc(self):
        retriever = ConcreteRetriever()
        doc = retriever._make_doc(
            doc_id="test123",
            title="Test Title",
            snippet="Test snippet",
            url="https://example.com",
            raw_content="full content",
            score=0.95,
        )
        assert doc["doc_id"] == "test123"
        assert doc["title"] == "Test Title"
        assert doc["source_type"] == "test"


class TestBrowserRetriever:
    @pytest.mark.asyncio
    async def test_retrieve(self):
        retriever = BrowserRetriever()
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_resp = mock_get.return_value.__aenter__.return_value
            mock_resp.text = "<html>test</html>"
            mock_resp.raise_for_status = lambda: None

            docs = await retriever.retrieve("test query")
            assert len(docs) >= 1
            assert docs[0]["source_type"] == "browser"


class TestRetrieverRegistry:
    def test_available_routes(self):
        from agentic_search.retrieval import get_available_routes

        routes = get_available_routes()
        assert "timeliness" in routes
        assert "academic" in routes
        assert "fallback" in routes
