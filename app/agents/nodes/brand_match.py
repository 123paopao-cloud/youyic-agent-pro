"""节点② 品牌匹配 Agent：评估热点与优益C品牌的匹配度。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, normalize_level, run_llm
from app.agents.state import AgentState
from app.knowledge.retriever import query_knowledge

SYS = """你是品牌策略专家。请依据「优益C品牌关键词库」，逐一评估给定热点与优益C品牌的匹配度。\
输出格式：
匹配等级：高 / 中 / 低（只填一个）
匹配分析：说明命中哪些品牌关键词、为什么是这个等级
可用热点：列出最值得做的 1-3 个热点
切入建议：每个可用热点给一个切入角度
判定口径：与肠道/久坐/饮食/校园年轻生活直接相关为高；可软性结合为中；无关或热点含负面争议为低。"""


def brand_match_node(state: AgentState) -> dict:
    add_step(state, "brand_match", "品牌匹配：评估热点契合度")
    keywords = query_knowledge("brand_keywords", state.get("user_request", "") + " 肠道 久坐 校园", k=6)

    output = run_llm(
        SYS,
        f"{keywords}\n\n热点摘要：\n{state.get('hotspot_summary', '')}",
        temperature=0.3,
        max_tokens=1200,
    )
    level = normalize_level(output, ("高", "中", "低"))
    return {"brand_match": output, "match_level": level}
