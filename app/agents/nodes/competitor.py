"""节点④ 竞品监测 Agent：监测竞品热点响应，给出差异化提醒。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, run_llm
from app.agents.state import AgentState
from app.tools.search import format_results, search_web

SYS = """你是竞争情报分析师。基于竞品动态材料，说明伊利、妙可蓝多等乳酸菌/乳制品品牌近期在相关热点上的动作，\
并指出优益C应该"跟进、规避还是差异化切入"。若材料中没有竞品信息，如实说明"暂未监测到直接响应"，不要编造。"""


def competitor_node(state: AgentState) -> dict:
    add_step(state, "competitor", "竞品监测：扫描对手响应")
    time_ctx = state.get("time_context", "")
    try:
        items, _ = search_web(
            f"{time_ctx} 伊利 乳酸菌 益生菌 妙可蓝多 营销 热点 活动", max_results=6
        )
        raw = format_results(items)
    except Exception as e:  # noqa: BLE001 - 竞品监测失败不应阻断主流程
        raw = f"竞品监测暂不可用：{e}"

    output = run_llm(
        SYS,
        f"热点方向：\n{state.get('brand_match', '')}\n\n竞品材料：\n{raw}",
        temperature=0.4,
        max_tokens=1000,
    )
    return {"competitor": output}
