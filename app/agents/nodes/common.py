"""节点共享辅助：LLM 调用、步骤记录、标记解析。"""
from __future__ import annotations

import re
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm


def add_step(state: dict, name: str, title: str) -> None:
    """记录一个执行步骤（供前端展示进度）。"""
    steps = state.get("steps", [])
    steps.append({"node": name, "title": title})
    state["steps"] = steps


def run_llm(system: str, user: str, temperature: float = 0.6, max_tokens: int = 2200) -> str:
    """以 system + user 消息调用大模型，返回文本。

    免费模型（智谱 Flash 系列）高峰期会 429 限流、网络偶发断连，
    这里做有限次退避重试：最多 5 次、等待 5/10/20/30/45 秒；其他错误直接抛出。
    """
    last_err: Exception | None = None
    waits = (5, 10, 20, 30, 45)
    for attempt in range(5):
        try:
            llm = get_llm(temperature=temperature, max_tokens=max_tokens)
            resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
            return resp.content.strip()
        except Exception as e:  # noqa: BLE001
            last_err = e
            msg = str(e)
            retriable = any(
                k in msg
                for k in (
                    "429", "1305", "1302", "访问量过大",
                    "Connection error", "Server disconnected",
                    "RemoteProtocolError", "timed out", "Timeout",
                )
            )
            if retriable:
                time.sleep(waits[attempt])
                continue
            raise
    raise last_err


def extract_tag(text: str, tag: str) -> str:
    """从 LLM 输出中提取「标签：值」形式的单行值。"""
    m = re.search(rf"{tag}\s*[:：]\s*(.+)", text)
    return m.group(1).strip() if m else ""


def normalize_level(text: str, options: tuple[str, ...]) -> str:
    """从文本里识别给定选项中的等级关键字，取第一个命中；否则返回最后一个（保守）。"""
    for opt in options:
        if opt in text:
            return opt
    return options[-1]
