"""可插拔的热点搜索层。

优先级：Tavily（有 Key，效果好） > 博查 Bocha（国内，有 Key） > DuckDuckGo（免费兜底）。
任一后端失败自动降级，保证「不额外注册也能跑通」。
"""
from __future__ import annotations

import os
from typing import Any

from app.config import get_settings


def _from_tavily(query: str, max_results: int) -> list[dict[str, Any]]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=get_settings().tavily_api_key)
    resp = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
    )
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "source": "tavily",
        }
        for r in resp.get("results", [])
    ]


def _from_bocha(query: str, max_results: int) -> list[dict[str, Any]]:
    import requests

    resp = requests.post(
        "https://api.bochaai.com/v1/web-search",
        headers={
            "Authorization": f"Bearer {get_settings().bocha_api_key}",
            "Content-Type": "application/json",
        },
        json={"query": query, "count": max_results, "summary": True},
        timeout=30,
    )
    resp.raise_for_status()
    pages = (
        resp.json().get("data", {}).get("webPages", {}).get("value", [])
    )
    return [
        {
            "title": p.get("name", ""),
            "url": p.get("url", ""),
            "content": p.get("summary") or p.get("snippet", ""),
            "source": "bocha",
        }
        for p in pages
    ]


def _from_ark_websearch(query: str, max_results: int) -> list[dict[str, Any]]:
    """火山方舟 Responses API 内置联网：只用 ARK key 即可搜索（需较新模型+开通联网插件）。

    方舟联网偶发连接错误，这里做最多 3 次指数退避重试，保证稳定性。
    """
    import time as _time

    from openai import OpenAI

    s = get_settings()
    # 必须显式设置超时（默认600s会导致网络挂起时整个流程卡死）
    client = OpenAI(api_key=s.ark_api_key, base_url=s.ark_base_url, timeout=25.0, max_retries=0)
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            resp = client.responses.create(
                model=s.ark_model,
                input=[
                    {
                        "role": "user",
                        "content": f"请联网搜索以下主题，列出 {max_results} 条相关结果，"
                        f"每条给出标题、来源网址和内容摘要：{query}",
                    }
                ],
                tools=[{"type": "web_search", "max_keyword": 2}],
                timeout=25.0,
            )
            text_parts = []
            for item in getattr(resp, "output", []) or []:
                for c in getattr(item, "content", []) or []:
                    t = getattr(c, "text", "")
                    if t:
                        text_parts.append(t)
            combined = "\n".join(text_parts)
            if combined:
                return [
                    {
                        "title": f"方舟联网：{query}",
                        "url": "volcengine-ark",
                        "content": combined,
                        "source": "ark_websearch",
                    }
                ]
            raise RuntimeError("方舟联网未返回内容（可能未开通联网内容插件或模型不支持）")
        except Exception as e:  # noqa: BLE001
            last_err = e
            _time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"方舟联网重试3次仍失败：{last_err}")


def _from_ddg(query: str, max_results: int) -> list[dict[str, Any]]:
    import signal

    from ddgs import DDGS

    def _timeout_handler(*_a, **_k):
        raise TimeoutError("duckduckgo 超时")

    # 国内网络访问 DDG 常挂起，设 12 秒硬超时，避免拖垮降级路径
    old = signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        signal.alarm(12)
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="cn-zh"))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "content": r.get("body", ""),
            "source": "duckduckgo",
        }
        for r in results
    ]


def search_web(query: str, max_results: int = 8) -> tuple[list[dict[str, Any]], str]:
    """执行网页搜索，返回 (结果列表, 实际使用的后端名)。"""
    s = get_settings()
    backends: list[tuple[str, Any]] = []
    if s.tavily_api_key:
        backends.append(("tavily", _from_tavily))
    if s.bocha_api_key:
        backends.append(("bocha", _from_bocha))
    # 方舟内置联网（默认关闭：账户欠费时会卡超时；需要时 .env 设 USE_ARK_WEBSEARCH=1）
    if s.llm_ready and os.getenv("USE_ARK_WEBSEARCH", "0") == "1":
        backends.append(("ark_websearch", _from_ark_websearch))
    backends.append(("duckduckgo", _from_ddg))  # 海外环境兜底

    errors: list[str] = []
    for name, fn in backends:
        try:
            items = fn(query, max_results)
            if items:
                return items, name
        except Exception as e:  # noqa: BLE001 - 降级到下一后端
            errors.append(f"{name}: {e}")
    raise RuntimeError("所有搜索后端均失败：" + " | ".join(errors))


def format_results(items: list[dict[str, Any]]) -> str:
    """把搜索结果拼成给 LLM 的文本。"""
    lines = []
    for i, r in enumerate(items, 1):
        lines.append(
            f"[{i}] 标题：{r['title']}\n    来源：{r['url']}\n    摘要：{r['content']}"
        )
    return "\n".join(lines)
