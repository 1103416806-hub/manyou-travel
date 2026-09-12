from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agentic_search.config import settings
from agentic_search.llm import get_llm_lite
from agentic_search.state import SearchState

logger = logging.getLogger(__name__)

REFLECTION_SYSTEM_PROMPT = """你是一个搜索结果质量评估专家。

请对当前搜索结果进行三维评估：

1. Relevance（相关性）：证据与 query 的相关度 (0-1)
2. Sufficiency（充分性）：信息是否足以回答 query (0-1)
3. Consistency（一致性）：证据之间是否一致 (0-1)

同时识别信息缺口（gaps）：还缺少什么信息？

请输出 JSON 格式：
{{
    "relevance": 0.0-1.0,
    "sufficiency": 0.0-1.0,
    "consistency": 0.0-1.0,
    "gaps": ["缺口1", "缺口2", ...],
    "decision": "continue" | "stop",
    "reasoning": "评估理由"
}}

判断标准：
- 如果三个分数均 >= {threshold}，decision 为 "stop"
- 否则 decision 为 "continue"，并在 gaps 中说明缺少什么
""".strip()


async def reflection_node(state: SearchState) -> dict:
    llm = get_llm_lite()
    ranked_docs = state.get("ranked_docs", [])

    docs_summary = "\n".join(
        f"[{i}] ({d.get('source_type', 'unknown')}) {d.get('title', '')}\n   {d.get('snippet', '')[:200]}"
        for i, d in enumerate(ranked_docs)
    )

    messages = [
        SystemMessage(content=REFLECTION_SYSTEM_PROMPT.format(threshold=settings.REFLECTION_STOP_THRESHOLD)),
        HumanMessage(content=f"Query: {state['query']}\n\n搜索结果:\n{docs_summary}"),
    ]

    response = await llm.ainvoke(messages)
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"relevance": 0.5, "sufficiency": 0.5, "consistency": 0.5, "gaps": [], "decision": "continue", "reasoning": ""}

    relevance = float(result.get("relevance", 0.5))
    sufficiency = float(result.get("sufficiency", 0.5))
    consistency = float(result.get("consistency", 0.5))
    confidence = (relevance + sufficiency + consistency) / 3.0

    decision = result.get("decision", "continue")
    if confidence >= settings.REFLECTION_STOP_THRESHOLD:
        decision = "stop"

    logger.info("Reflection: rel=%.2f suf=%.2f con=%.2f conf=%.2f decision=%s gaps=%s",
                relevance, sufficiency, consistency, confidence, decision, result.get("gaps", []))

    return {
        "reflection_scores": {
            "relevance": relevance,
            "sufficiency": sufficiency,
            "consistency": consistency,
        },
        "gaps": result.get("gaps", []),
        "decision": decision,
        "confidence": confidence,
    }
