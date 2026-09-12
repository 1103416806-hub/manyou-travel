from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agentic_search.llm import get_llm_lite
from agentic_search.state import SearchState

logger = logging.getLogger(__name__)

QUERY_SYSTEM_PROMPT = """你是一个 Query 改写和意图分类专家。

你的职责：
1. 意图分类：判断 query 属于哪类（时效/实时/学术/代码/反馈/通用）
2. Query 改写：根据意图使用合适的改写策略

改写策略：
- Multi-Query：生成 3-5 个变体查询（RAG Fusion 基础）
- HyDE：如果是文档检索场景，生成假设性文档描述
- Step-Back：如果是细节问题，先抽象化
- Decomposition：如果是复合问题，拆解为子问题

请输出 JSON 格式：
{{
    "intent": "timeliness|realtime|academic|code|feedback|general",
    "sub_queries": ["改写后的查询1", "改写后的查询2", ...],
    "source_routing": ["timeliness", "academic", ...],
    "rewrite_strategy": "multi_query|hyde|step_back|decomposition",
    "hyde_document": "如果是 HyDE 策略，生成假设文档"
}}

可用路由源：timeliness, realtime, academic, code, feedback, private, fallback
""".strip()


INTENT_ROUTING_MAP = {
    "timeliness": ["timeliness", "fallback"],
    "realtime": ["realtime", "timeliness"],
    "academic": ["academic", "private"],
    "code": ["code", "academic"],
    "feedback": ["feedback", "timeliness"],
    "general": ["timeliness", "academic", "fallback"],
}


async def query_node(state: SearchState) -> dict:
    llm = get_llm_lite()

    messages = [
        SystemMessage(content=QUERY_SYSTEM_PROMPT),
        HumanMessage(content=f"Query: {state['query']}"),
    ]

    if state.get("gaps"):
        messages.append(HumanMessage(content=f"当前信息缺口: {json.dumps(state['gaps'], ensure_ascii=False)}"))

    response = await llm.ainvoke(messages)
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "intent": "general",
            "sub_queries": [state["query"]],
            "source_routing": ["timeliness", "fallback"],
            "rewrite_strategy": "multi_query",
        }

    intent = result.get("intent", "general")
    if not result.get("source_routing"):
        result["source_routing"] = INTENT_ROUTING_MAP.get(intent, ["timeliness", "fallback"])

    logger.info("Query: intent=%s, sub_queries=%s, routing=%s", intent, result.get("sub_queries", []), result["source_routing"])

    return {
        "intent": intent,
        "sub_queries": result.get("sub_queries", [state["query"]]),
        "source_routing": result["source_routing"],
    }
