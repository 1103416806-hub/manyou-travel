from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agentic_search.llm import get_llm_pro
from agentic_search.state import SearchState

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """你是一个专业答案生成专家。

基于提供的证据，生成带引用的答案。

规则：
1. 每个结论必须带 [source_id] 引用标记
2. 引用冲突时按优先级：官方 > 权威媒体 > 社区；新 > 旧
3. 禁止引用未在证据中出现的 URL
4. 如果证据不足以完全回答，明确说明

输出 JSON 格式：
{{
    "answer": "带 [0] [1] 引用标记的答案",
    "citations": [
        {{"source_id": "0", "url": "...", "title": "...", "snippet": "...", "source_type": "..."}},
        ...
    ]
}}
""".strip()


async def synthesis_node(state: SearchState) -> dict:
    llm = get_llm_pro()
    ranked_docs = state.get("ranked_docs", [])

    evidence_text = "\n".join(
        f"[{i}] ({d.get('source_type', 'unknown')}) {d.get('title', '')}\n    URL: {d.get('url', '')}\n    {d.get('snippet', '')}"
        for i, d in enumerate(ranked_docs)
    )

    messages = [
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=f"Query: {state['query']}\n\n证据:\n{evidence_text}"),
    ]

    response = await llm.ainvoke(messages)
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "answer": response.content,
            "citations": [],
        }

    citations = result.get("citations", [])
    valid_citations = []
    doc_urls = {d.get("url", "") for d in ranked_docs}
    for cit in citations:
        if cit.get("url", "") in doc_urls:
            valid_citations.append(cit)

    logger.info("Synthesis: generated answer with %d/%d valid citations", len(valid_citations), len(citations))

    return {
        "answer": result.get("answer", ""),
        "citations": valid_citations,
    }
