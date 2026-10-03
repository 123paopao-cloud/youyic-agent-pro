"""节点⑤ 策略生成 Agent：生成多个可执行营销策略方向与多平台内容。"""
from __future__ import annotations

from app.agents.nodes.common import add_step, run_llm
from app.agents.state import AgentState
from app.knowledge.retriever import query_knowledge

SYS = """你是优益C的首席内容策略师。基于已通过合规审查的热点，产出 3-5 个差异化营销策略方向。
每个方向包含：方向名称、热点依据、目标人群、主攻平台、内容形式、可直接使用的标题（2-3个）、正文/脚本要点、植入方式。
至少给出一个完整的小红书图文范例和一个抖音口播要点。
硬性要求：卖点用第一人称体验口吻（"我觉得""喝完舒服多了"），禁止疾病/保健/治疗功效宣称和极限词；
若合规官给了黄灯修改意见，必须严格按意见措辞。"""


def strategy_node(state: AgentState) -> dict:
    add_step(state, "strategy", "策略生成：产出营销方案")
    assets = query_knowledge("brand_assets", state.get("user_request", "") + " 卖点 场景", k=6)
    cases = query_knowledge("hit_cases", state.get("user_request", "") + " 爆款 结构", k=4)

    yellow_hint = ""
    if state.get("compliance_level") == "黄":
        yellow_hint = f"\n【必须遵守的合规修改意见】\n{state.get('compliance_note', '')}"

    output = run_llm(
        SYS,
        f"{assets}\n\n{cases}\n\n可用热点与切入：\n{state.get('brand_match', '')}"
        f"\n竞品差异化提示：\n{state.get('competitor', '')}{yellow_hint}",
        temperature=0.7,
        max_tokens=3000,
    )
    return {"strategy": output}
