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
