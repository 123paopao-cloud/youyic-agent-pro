"""LangGraph 主图：六节点顺序流转 + 合规门禁条件路由。

流程：
  START → 热点发现 → 品牌匹配 → 安全合规
      ├─ 红灯 → 门禁拦截 → END
      └─ 黄/绿灯 → 竞品监测 → 策略生成 → 效果预判 → 报告组装 → END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.brand_match import brand_match_node
from app.agents.nodes.compliance import compliance_node
from app.agents.nodes.competitor import competitor_node
from app.agents.nodes.hotspot import hotspot_node
from app.agents.nodes.prediction import prediction_node
from app.agents.nodes.report import blocked_gate_node, report_node
from app.agents.nodes.strategy import strategy_node
from app.agents.state import AgentState


def route_after_compliance(state: AgentState) -> str:
    """合规门禁：红灯拦截，黄/绿灯进入主链路。"""
    level = state.get("compliance_level", "绿")
    if level == "红":
        return "blocked"
    return "main"


def build_graph():
    g = StateGraph(AgentState)

    # 节点（每个节点即一个专业 Agent）
    g.add_node("hotspot", hotspot_node)
    g.add_node("brand_match", brand_match_node)
    g.add_node("compliance", compliance_node)
    g.add_node("blocked_gate", blocked_gate_node)
    g.add_node("competitor", competitor_node)
    g.add_node("strategy", strategy_node)
    g.add_node("prediction", prediction_node)
    g.add_node("report", report_node)

    # 固定边
    g.add_edge(START, "hotspot")
    g.add_edge("hotspot", "brand_match")
    g.add_edge("brand_match", "compliance")

    # 合规门禁（条件边）
    g.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {"blocked": "blocked_gate", "main": "competitor"},
    )
    g.add_edge("blocked_gate", END)

    # 主链路
    g.add_edge("competitor", "strategy")
    g.add_edge("strategy", "prediction")
    g.add_edge("prediction", "report")
    g.add_edge("report", END)

    return g.compile()


# 编译后的图单例
compiled_graph = build_graph()
