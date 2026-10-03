"""终点节点：组装《热点策略报告》（纯 Python 拼接，省一次模型调用）。"""
from __future__ import annotations

from app.agents.nodes.common import add_step
from app.agents.state import AgentState


def _blocked_report(state: dict) -> str:
    return f"""# 热点合规审查结果：不建议追（红灯拦截）

## 拟评估热点
{state.get('hotspot_summary', '')}

## 品牌匹配
{state.get('brand_match', '')}

## 合规门禁结论（红灯）
{state.get('compliance_note', '')}

---
系统已在内容生产前拦截该方向，避免品牌风险。如需继续，请更换合规的热点后重新发起。"""


def _full_report(state: dict) -> str:
    yellow = "\n> 注意：本方案为黄灯修改后放行，措辞已按合规意见调整。" if state.get(
        "compliance_level"
    ) == "黄" else ""
    return f"""# 优益C 热点策略报告
{yellow}

## 一、近期热点洞察
{state.get('hotspot_summary', '')}

## 二、品牌匹配分析
{state.get('brand_match', '')}

## 三、安全合规审查（{state.get('compliance_level', '绿')}灯通过）
{state.get('compliance_note', '')}

## 四、竞品监测与差异化
{state.get('competitor', '')}

## 五、营销策略方案
{state.get('strategy', '')}

## 六、效果预判
{state.get('prediction', '')}

---
*本报告由「优益C 热点策略智能体」自动生成：热点发现 → 品牌匹配 → 安全合规 → 竞品监测 → 策略生成 → 效果预判。*"""


def blocked_gate_node(state: AgentState) -> dict:
    """红灯分支的终点：输出拦截报告。"""
    add_step(state, "blocked", "门禁拦截：终止内容生产")
    return {"blocked": True, "final_report": _blocked_report(state)}


def report_node(state: AgentState) -> dict:
    """绿灯/黄灯分支的终点：输出完整报告。"""
    add_step(state, "report", "报告组装：生成策略报告")
    return {"blocked": False, "final_report": _full_report(state)}
