"""节点③ 安全合规 Agent（安全合规官）：红黄绿风险评级，作为强制门禁。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, normalize_level, run_llm
from app.agents.state import AgentState
from app.knowledge.retriever import query_knowledge

SYS = """你是品牌内容安全合规官，极其严谨。依据「合规红线库」，审查这些热点及拟切入方向是否存在：\
违法极限词、普通食品违规宣称疾病/保健/治疗功效、灾难或悲情营销、低俗擦边、性别或群体冒犯、IP侵权等风险。
输出格式：
合规评级：绿 / 黄 / 红（只填一个）
风险说明：指出具体风险点（无风险也要说明检查了哪些项）
修改建议：黄灯必须给出可执行的措辞/角度修改；红灯说明为何应放弃。
口径：触碰法律红线、功效宣称、灾难营销、擦边、侵权为红；角度可行但措辞有风险为黄；无风险为绿。"""


def compliance_node(state: AgentState) -> dict:
    add_step(state, "compliance", "安全合规：红黄绿风险门禁")
    rules = query_knowledge("compliance_rules", state.get("user_request", "") + " 功效 宣称 极限词 翻车", k=8)

    output = run_llm(
        SYS,
        f"{rules}\n\n品牌匹配结论：\n{state.get('brand_match', '')}\n\n热点摘要：\n{state.get('hotspot_summary', '')}",
        temperature=0.2,
        max_tokens=1200,
    )
    level = normalize_level(output, ("绿", "黄", "红"))
    return {"compliance_level": level, "compliance_note": output}
