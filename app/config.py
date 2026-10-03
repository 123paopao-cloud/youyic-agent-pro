"""全局配置：从 .env / 环境变量读取，所有密钥只在这里集中管理。"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（app/ 的上一级）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "app", "data")

# 显式加载 .env
load_dotenv(os.path.join(ROOT_DIR, ".env"))


def _inject_streamlit_secrets() -> None:
    """Streamlit Community Cloud 兼容：把 st.secrets 注入环境变量。

    云端部署时 .env 不会上传（被 .gitignore 排除），密钥通过 Streamlit 控制台
    Secrets 配置。st.secrets 不会自动写入 os.environ，BaseSettings 读不到，
    这里在 Settings 实例化前显式注入（setdefault 不覆盖已有真实环境变量）。
    非 Streamlit 环境（本地脚本 / FastAPI）无 streamlit 模块时安全跳过。
    """
    try:
        import streamlit as st  # 仅 Streamlit 环境存在
    except Exception:
        return
    try:
        for k in st.secrets:
            v = st.secrets[k]
            if isinstance(v, str) and v:
                os.environ.setdefault(k, v)
    except Exception:
        pass


_inject_streamlit_secrets()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    # ---- 大模型（默认智谱，OpenAI 兼容接口）----
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="glm-4.7-flash", alias="LLM_MODEL")
    llm_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", alias="LLM_BASE_URL"
    )

    # ---- 备选：火山方舟 / 豆包（历史兼容）----
    ark_api_key: str = Field(default="", alias="ARK_API_KEY")
    ark_model: str = Field(default="doubao-seed-1-6-250615", alias="ARK_MODEL")
    ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3", alias="ARK_BASE_URL"
    )
    ark_embed_model: str = Field(default="", alias="ARK_EMBED_MODEL")

    # ---- 搜索 ----
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    bocha_api_key: str = Field(default="", alias="BOCHA_API_KEY")

    # ---- 服务 ----
    api_port: int = Field(default=8000, alias="API_PORT")
    daily_trial_limit: int = Field(default=8, alias="DAILY_TRIAL_LIMIT")

    @property
    def active_key(self) -> str:
        """优先使用 LLM_*（智谱），其次 ARK_*（方舟）。"""
        return self.llm_api_key or self.ark_api_key

    @property
    def active_model(self) -> str:
        return self.llm_model if self.llm_api_key else self.ark_model

    @property
    def active_base_url(self) -> str:
        return self.llm_base_url if self.llm_api_key else self.ark_base_url

    @property
    def llm_ready(self) -> bool:
        key = self.active_key
        return bool(key) and not key.startswith("在此") and not key.startswith("这里")


@lru_cache
def get_settings() -> Settings:
    return Settings()
