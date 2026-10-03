"""大模型接入：统一走 OpenAI 兼容接口（默认智谱 GLM-4.7-Flash，备选火山方舟豆包）。"""
from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import get_settings


@lru_cache
def get_llm(temperature: float = 0.6, max_tokens: int = 2200) -> ChatOpenAI:
    """返回大模型单例。

    - 配置了 LLM_*（智谱）→ 用智谱 OpenAI 兼容接口
    - 否则回退 ARK_*（火山方舟）→ 用方舟 OpenAI 兼容接口
    """
    s = get_settings()
    return ChatOpenAI(
        model=s.active_model,
        api_key=s.active_key,
        base_url=s.active_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=120,
        max_retries=0,  # 关闭库内部自动重试，避免与 run_llm 的手动退避叠加触发限流
        request_timeout=120,
    )


@lru_cache
def get_embeddings() -> OpenAIEmbeddings | None:
    """返回向量化模型；未配置则返回 None，由知识库自动降级为 BM25。"""
    s = get_settings()
    if not s.ark_embed_model or not s.llm_ready:
        return None
    return OpenAIEmbeddings(
        model=s.ark_embed_model,
        api_key=s.active_key,
        base_url=s.active_base_url,
    )
