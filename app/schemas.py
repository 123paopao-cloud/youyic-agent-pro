"""请求/响应数据模型。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    message: str = Field(..., description="用户的营销需求/提问")
    time_context: str = Field(default="", description="时间上下文，如 国庆假期、开学季")


class RunResponse(BaseModel):
    ok: bool
    blocked: bool = False
    final_report: str
    steps: list[dict[str, Any]] = []
    error: str = ""
