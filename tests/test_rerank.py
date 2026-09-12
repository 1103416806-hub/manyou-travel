
from agentic_search.rerank.rrf import rrf_fuse
from agentic_search.state import CandidateDoc


def _doc(doc_id: str, score: float = 0.0) -> CandidateDoc:
    return CandidateDoc(
        doc_id=doc_id,
        title=f"Title {doc_id}",
        snippet=f"Snippet {doc_id}",
        url=f"https://example.com/{doc_id}",
        source_type="test",
        raw_content="",
        score=score,
    )


class TestRRF:
    def test_basic_fusion(self):
        source_results = {
            "source_a": [_doc("a1"), _doc("a2")],
            "source_b": [_doc("b1")],
        }
        result = rrf_fuse(source_results)
        assert len(result) == 3
        assert result[0]["doc_id"] == "a1"

    def test_deduplication(self):
        source_results = {
            "source_a": [_doc("same_doc")],
            "source_b": [_doc("same_doc")],
        }
        result = rrf_fuse(source_results)
        assert len(result) == 1

    def test_empty_input(self):
        result = rrf_fuse({})
        assert result == []

    def test_custom_k(self):
        source_results = {"s": [_doc("d1"), _doc("d2")]}
        result = rrf_fuse(source_results, k=100)
        assert len(result) == 2
