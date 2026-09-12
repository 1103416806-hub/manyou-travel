from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agentic_search.state import CandidateDoc


class BaseRetriever(ABC):
    source_type: str = "unknown"

    @abstractmethod
    async def retrieve(self, query: str, max_results: int = 10, **kwargs: Any) -> list[CandidateDoc]:
        raise NotImplementedError

    def _make_doc(
        self,
        doc_id: str,
        title: str,
        snippet: str,
        url: str,
        raw_content: str = "",
        score: float = 0.0,
    ) -> CandidateDoc:
        return CandidateDoc(
            doc_id=doc_id,
            title=title,
            snippet=snippet,
            url=url,
            source_type=self.source_type,
            raw_content=raw_content,
            score=score,
        )
