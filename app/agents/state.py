"""LangGraph 全局状态：在六个节点之间流转的数据。"""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # 输入
    user_request: str        # 用户原始需求（如"最近有什么热点，帮我出几条小红书方案"）
    time_context: str        # 时间上下文（如"国庆假期"）

    # ① 热点发现
    hotspots: str            # 热点搜索结果（拼接文本）
    hotspot_backend: str     # 实际使用的搜索后端
    hotspot_summary: str     # 热点结构化摘要

    # ② 品牌匹配
    brand_match: str         # 品牌匹配分析
    match_level: str         # 高 / 中 / 低

    # ③ 安全合规
    compliance_level: str    # 绿 / 黄 / 红
    compliance_note: str     # 评级理由 + 修改建议

    # ④ 竞品监测
    competitor: str          # 竞品热点响应情况

    # ⑤ 策略生成
    strategy: str            # 3-5 个营销策略方向 + 多平台内容

    # ⑥ 效果预判
    prediction: str          # 互动率区间 / 优先平台 / 爆款指数

    # 输出
    final_report: str        # 最终《热点策略报告》
    blocked: bool            # 是否被合规门禁拦截

    # 过程追踪（前端展示"正在做什么"）
    steps: list[dict[str, Any]]
