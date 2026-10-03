"""节点⑥ 效果预判 Agent：给出互动预期、优先平台与爆款指数。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, run_llm
from app.agents.state import AgentState
from app.knowledge.retriever import query_knowledge

SYS = """你是数据驱动的传播效果分析师。结合热点热度阶段、平台特性、历史爆款规律，对每个策略方向给出预判。
输出：
优先平台排序：并说明理由
爆款指数：对每个方向打 1-10 分并说明依据
预期表现：用定性区间描述（如"互动潜力高/中/低"），不要编造精确的百分比数据
成败关键：列出提升表现的 3 个要点和需要规避的风险。"""


def prediction_node(state: AgentState) -> dict:
    add_step(state, "prediction", "效果预判：评估传播潜力")
    cases = query_knowledge("hit_cases", "爆款 规律 平台", k=4)

    output = run_llm(
        SYS,
        f"{cases}\n\n热点摘要：\n{state.get('hotspot_summary', '')}\n\n策略方案：\n{state.get('strategy', '')}",
        temperature=0.4,
        max_tokens=1400,
    )
    return {"prediction": output}
