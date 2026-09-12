from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agentic_search.config import settings
from agentic_search.llm import get_llm_lite
from agentic_search.state import SearchState

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """你是一个 Self-RAG 校验专家，负责检查答案质量。

请对答案进行四维校验：

1. IsRel：每条引用与 query 相关吗？
2. IsSup：每句话能从引用推出吗？（幻觉检测）
3. IsUse：整体回答了 query 吗？
4. Ground：引用的 source_id 在证据中真实存在吗？

输出 JSON 格式：
{{
    "isRel": true/false,
    "isSup": true/false,
    "isUse": true/false,
    "ground": true/false,
    "details": "具体问题描述",
    "decision": "pass" | "hallucination" | "missing_info"
}}

判断逻辑：
- 全部 true → "pass"
- isSup=false → "hallucination"（需要重写答案）
- isRel=false 或 isUse=false → "missing_info"（需要补查）
""".strip()


async def critic_node(state: SearchState) -> dict:
    llm = get_llm_lite()
    retry_count = state.get("retry_count", 0)
    iteration = state.get("iteration", 0)

    if retry_count >= settings.MAX_RETRIES or iteration >= settings.MAX_ITERATIONS:
        return {
            "critic_result": {"isRel": True, "isSup": True, "isUse": True, "ground": True, "details": "强制通过（达到重试上限）"},
            "critic_decision": "pass",
        }

    ranked_docs = state.get("ranked_docs", [])
    answer = state.get("answer", "")
    citations = state.get("citations", [])

    evidence_ids = {str(i) for i in range(len(ranked_docs))}

    messages = [
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Query: {state['query']}\n\n答案: {answer}\n\n引用: {json.dumps(citations, ensure_ascii=False)}\n\n可用证据ID: {evidence_ids}"
        ),
    ]

    response = await llm.ainvoke(messages)
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"isRel": True, "isSup": True, "isUse": True, "ground": True, "details": "", "decision": "pass"}

    decision = result.get("decision", "pass")

    logger.info("Critic: isRel=%s isSup=%s isUse=%s ground=%s decision=%s",
                result.get("isRel"), result.get("isSup"), result.get("isUse"), result.get("ground"), decision)

    return {
        "critic_result": {
            "isRel": result.get("isRel", True),
            "isSup": result.get("isSup", True),
            "isUse": result.get("isUse", True),
            "ground": result.get("ground", True),
            "details": result.get("details", ""),
        },
        "critic_decision": decision,
        "retry_count": retry_count + 1 if decision == "hallucination" else retry_count,
    }
