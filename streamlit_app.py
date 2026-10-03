"""优益C 热点策略智能体 - Streamlit 免注册聊天界面。

两种运行模式（自动选择）：
  1. 直连模式（默认，部署最简单）：本进程直接运行 LangGraph，实时展示六步进度。
  2. API 模式：若检测到 FastAPI（设置 API_BASE_URL），则走标准后端接口。

本地运行：streamlit run streamlit_app.py
"""
from __future__ import annotations

import os
import sys

import requests
import streamlit as st

# 确保能 import app 包（项目根目录）
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.config import get_settings  # noqa: E402

BRAND_GREEN = "#1B7A4A"
QUICK_QUESTIONS = [
    "最近有什么热点？帮我出3条小红书营销方案",
    "国庆出游季，优益C可以怎么借势营销？",
    "帮我写一条抖音口播脚本，主题是久坐肠活动",
    "考试周快到了，给几个校园营销点子",
    "分析一下优益C在大学生里的目标人群画像",
]


# ---------------------------------------------------------------- 页面配置
st.set_page_config(
    page_title="优益C校园营销助手",
    page_icon="🟢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: linear-gradient(180deg,#F2F7F3 0%,#FFFFFF 60%); }}
      [data-testid="stChatMessage"] {{ border-radius: 14px; }}
      .brand-header {{ text-align:center; padding: 8px 0 4px; }}
      .brand-header h1 {{ color:{BRAND_GREEN}; font-weight:900; font-size:26px; margin:0; }}
      .brand-header p {{ color:#5A7A66; font-size:13px; margin:4px 0 0; }}
      .quick-pill {{ display:inline-block; background:#EAF5EE; border:1px solid #C8E2D2;
        color:{BRAND_GREEN}; border-radius:18px; padding:7px 14px; margin:4px; font-size:13px; }}
      .footer-note {{ text-align:center; color:#94A89C; font-size:11px; margin-top:18px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- 会话状态
def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "use_count" not in st.session_state:
        st.session_state.use_count = 0


init_state()
settings = get_settings()
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")


def use_api() -> bool:
    """检测 FastAPI 是否可用。"""
    if not API_BASE_URL:
        return False
    try:
        return requests.get(f"{API_BASE_URL}/api/health", timeout=2).json().get("ok", False)
    except Exception:
        return False


API_MODE = use_api()


# ---------------------------------------------------------------- 直连模式：运行 graph
def run_direct(message: str, time_ctx: str, status_container) -> tuple[str, bool]:
    from app.agents.graph import compiled_graph

    initial = {"user_request": message, "time_context": time_ctx, "steps": []}
    final_state: dict = {}
    done_titles: set[str] = set()
    for state in compiled_graph.stream(initial, stream_mode="values"):
        final_state = state
        for step in state.get("steps", []):
            if step["title"] not in done_titles:
                done_titles.add(step["title"])
                status_container.update(label="正在进行：" + step["title"])
    return final_state.get("final_report", ""), final_state.get("blocked", False)


# ---------------------------------------------------------------- API 模式
def run_api(message: str, time_ctx: str) -> tuple[str, bool, str]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/run",
            json={"message": message, "time_context": time_ctx},
            timeout=180,
        )
        data = resp.json()
        if not data.get("ok"):
            return "", False, data.get("error", "后端错误")
        return data.get("final_report", ""), data.get("blocked", False), ""
    except Exception as e:  # noqa: BLE001
        return "", False, str(e)


# ---------------------------------------------------------------- 界面头部
st.markdown(
    """
    <div class="brand-header">
      <h1>优益C 校园营销助手</h1>
      <p>热点发现 · 品牌匹配 · 安全合规 · 策略生成 · 效果预判</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 关于作品")
    st.write("蒙牛优益C杯 · 全域AI应用创新赛道参赛作品")
    st.write(f"运行模式：{'API（FastAPI）' if API_MODE else '直连（LangGraph）'}")
    if not settings.llm_ready:
        st.warning("尚未配置模型 API Key，请在 .env / 云端 Secrets 填入 LLM_API_KEY")
    st.caption(f"本次会话已使用 {st.session_state.use_count} 次")

# 快捷问题
if not st.session_state.messages:
    st.markdown('<div style="text-align:center;margin:10px 0 6px;">试试这些 👇</div>',
                unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(QUICK_QUESTIONS[:4]):
        if cols[i % 2].button(q, key=f"q{i}", use_container_width=True):
            st.session_state["_pending"] = q

# 历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 每日/会话上限保护
limit = settings.daily_trial_limit
over_limit = limit > 0 and st.session_state.use_count >= limit


# ---------------------------------------------------------------- 处理输入
def handle(message: str) -> None:
    st.session_state.use_count += 1
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.markdown(message)

    with st.chat_message("assistant"):
        if API_MODE:
            with st.spinner("智能体正在完成热点分析与方案生成…"):
                report, blocked, err = run_api(message, "")
            if err:
                st.error(f"运行失败：{err}")
            else:
                if blocked:
                    st.warning("该热点已被安全合规门禁拦截")
                st.markdown(report)
                result = report
        else:
            with st.status("智能体启动…", expanded=True) as status:
                report, blocked = run_direct(message, "", status)
                status.update(label="完成 ✅", state="complete", expanded=False)
            if blocked:
                st.warning("该热点已被安全合规门禁拦截")
            st.markdown(report)
            result = report

    st.session_state.messages.append({"role": "assistant", "content": result if not API_MODE else report})


pending = st.session_state.pop("_pending", None)
user_input = st.chat_input("输入你的营销需求，例如：最近热点+小红书方案…", disabled=over_limit)

if over_limit:
    st.info(f"为保护演示额度，本次会话体验上限为 {limit} 次。刷新页面可重新计数。")

if pending:
    handle(pending)
elif user_input:
    handle(user_input)

st.markdown(
    '<div class="footer-note">本智能体面向企业营销/运营人员，自动完成热点到方案的全流程</div>',
    unsafe_allow_html=True,
)
