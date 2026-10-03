"""FastAPI 后端：封装 LangGraph，保护大模型密钥，提供同步与流式接口。"""
from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.agents.graph import compiled_graph
from app.config import get_settings
from app.schemas import RunRequest, RunResponse

app = FastAPI(title="优益C 热点策略智能体 API", version="1.0.0")

# 允许前端（Streamlit/任意网页）跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    s = get_settings()
    return {
        "ok": True,
        "llm_ready": s.llm_ready,
        "model": s.ark_model,
        "daily_trial_limit": s.daily_trial_limit,
    }


@app.post("/api/run", response_model=RunResponse)
def run(req: RunRequest) -> RunResponse:
    """一次性运行完整链路，返回最终报告。"""
    s = get_settings()
    if not s.llm_ready:
        return RunResponse(ok=False, final_report="", error="后端尚未配置火山方舟 ARK_API_KEY")
    try:
        final_state = compiled_graph.invoke(
            {"user_request": req.message, "time_context": req.time_context, "steps": []}
        )
        return RunResponse(
            ok=True,
            blocked=final_state.get("blocked", False),
            final_report=final_state.get("final_report", ""),
            steps=final_state.get("steps", []),
        )
    except Exception as e:  # noqa: BLE001
        return RunResponse(ok=False, final_report="", error=str(e))


@app.post("/api/stream")
def stream(req: RunRequest) -> EventSourceResponse:
    """SSE 流式：每完成一个节点推送一次进度，最后推送完整报告。"""
    s = get_settings()

    def gen():
        if not s.llm_ready:
            yield {"event": "error", "data": json.dumps({"error": "后端尚未配置 ARK_API_KEY"})}
            return
        try:
            final_state: dict = {}
            initial = {"user_request": req.message, "time_context": req.time_context, "steps": []}
            for state in compiled_graph.stream(initial, stream_mode="values"):
                final_state = state
                steps = state.get("steps", [])
                if steps:
                    yield {"event": "step", "data": json.dumps(steps[-1], ensure_ascii=False)}
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "final_report": final_state.get("final_report", ""),
                        "blocked": final_state.get("blocked", False),
                        "steps": final_state.get("steps", []),
                    },
                    ensure_ascii=False,
                ),
            }
        except Exception as e:  # noqa: BLE001
            yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(gen())


@app.get("/")
def root() -> dict:
    return {"service": "优益C 热点策略智能体", "docs": "/docs", "health": "/api/health"}
