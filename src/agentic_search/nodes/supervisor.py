from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agentic_search.config import settings
from agentic_search.llm import get_llm_pro
from agentic_search.state import SearchState

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """你是一个搜索任务的 Supervisor/Planner。

你的职责：
1. 首次进入：分析用户 query，生成搜索 DAG 计划
2. 中途进入：根据 Reflection 或 Critic 的反馈调整计划
3. 终止判断：当 iteration >= {max_iter} 或 confidence >= {conf_thresh} 时终止

请输出 JSON 格式：
{{
    "plan": {{
        "description": "搜索计划描述",
        "steps": ["步骤1", "步骤2", ...],
        "focus_areas": ["关注领域1", ...]
    }},
    "next_action": "query" | "end",
    "reasoning": "决策理由"
}}

当前状态：
- iteration: {iteration}
- confidence: {confidence}
- gaps: {gaps}
- critic_feedback: {critic_feedback}
""".strip()


async def supervisor_node(state: SearchState) -> dict:
    llm = get_llm_pro()
    iteration = state.get("iteration", 0)
    confidence = state.get("confidence", 0.0)
    gaps = state.get("gaps", [])
    critic_result = state.get("critic_result")

    if iteration >= settings.MAX_ITERATIONS or confidence >= settings.CONFIDENCE_THRESHOLD:
        logger.info("Supervisor: terminating (iter=%d, conf=%.2f)", iteration, confidence)
        return {"plan": state.get("plan"), "decision": "end"}

    logger.info("Supervisor: planning (iter=%d, conf=%.2f, gaps=%s)", iteration, confidence, gaps)

    critic_feedback = ""
    if critic_result:
        critic_feedback = json.dumps(critic_result, ensure_ascii=False)

    prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        max_iter=settings.MAX_ITERATIONS,
        conf_thresh=settings.CONFIDENCE_THRESHOLD,
        iteration=iteration,
        confidence=confidence,
        gaps=json.dumps(gaps, ensure_ascii=False),
        critic_feedback=critic_feedback,
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"用户 Query: {state['query']}"),
    ]

    response = await llm.ainvoke(messages)
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"plan": {"description": "默认搜索计划", "steps": [], "focus_areas": []}, "next_action": "query", "reasoning": ""}

    return {
        "plan": result.get("plan"),
        "iteration": iteration + 1,
    }
