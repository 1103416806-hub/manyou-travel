from __future__ import annotations

from typing import Optional, TypedDict


class Citation(TypedDict):
    source_id: str
    url: str
    title: str
    snippet: str
    source_type: str


class CandidateDoc(TypedDict):
    doc_id: str
    title: str
    snippet: str
    url: str
    source_type: str
    raw_content: str
    score: float


class ReflectionScores(TypedDict):
    relevance: float
    sufficiency: float
    consistency: float


class CriticResult(TypedDict):
    isRel: bool
    isSup: bool
    isUse: bool
    ground: bool
    details: str


class SearchState(TypedDict, total=False):
    query: str
    thread_id: str
    iteration: int
    retry_count: int

    plan: Optional[dict]
    intent: Optional[str]
    sub_queries: list[str]
    source_routing: list[str]

    candidates: list[CandidateDoc]
    ranked_docs: list[CandidateDoc]

    reflection_scores: Optional[ReflectionScores]
    gaps: list[str]
    decision: str

    answer: Optional[str]
    citations: list[Citation]
    confidence: float

    critic_result: Optional[CriticResult]
    critic_decision: str
