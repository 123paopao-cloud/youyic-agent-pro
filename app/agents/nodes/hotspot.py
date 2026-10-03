"""节点① 热点发现 Agent：搜索近期热点并结构化摘要。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, run_llm
from app.agents.state import AgentState
from app.tools.search import format_results, search_web

SUMMARIZE_SYS = """你是资深社交媒体热点分析师。基于搜索到的近期资讯，提炼出 3-6 个当前正在发生、\
且与年轻人/校园/消费/生活方式相关的热点。对每个热点输出：热点名称、所属平台或来源、热度阶段（上升/爆发/衰退）、\
核心内容一句话、可能的营销切入角度。只基于给定材料，不要编造没有的热点。"""


def hotspot_node(state: AgentState) -> dict:
    add_step(state, "hotspot", "热点发现：扫描近期热点")
    user_request = state.get("user_request", "")
    time_ctx = state.get("time_context", "")

    # 构造搜索词：结合时间上下文与用户需求
    query = f"{time_ctx} 近期 社交媒体 热点 年轻人 校园 话题".strip()
    if "小红书" in user_request:
        query = f"{time_ctx} 小红书 近期热门话题 校园 种草".strip()
    elif "抖音" in user_request:
        query = f"{time_ctx} 抖音 近期热点 挑战 话题".strip()

    backend = "unavailable"
    raw = ""
    try:
        items, backend = search_web(query, max_results=8)
        raw = format_results(items)
    except Exception as e:  # noqa: BLE001 - 搜索失败降级，不阻断流程
        raw = f"（本次实时热点搜索暂不可用：{e}。请基于品牌知识库生成方向性方案，并提示用户稍后重试以获得实时热点。）"
        backend = "degraded"

    summary = run_llm(
        SUMMARIZE_SYS,
        f"用户需求：{user_request}\n搜索到的资讯：\n{raw}",
        temperature=0.4,
        max_tokens=1400,
    )
    return {
        "hotspots": raw,
        "hotspot_backend": backend,
        "hotspot_summary": summary,
    }
