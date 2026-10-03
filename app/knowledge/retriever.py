"""知识库检索：默认 BM25 关键词检索（无需下载模型），配置 embedding 后升级为向量 RAG。

每个知识库对应 app/data/ 下一个目录，目录内 .txt/.md 即知识内容。
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

from app.config import DATA_DIR

# 四个知识库（目录名 + 中文名）
KNOWLEDGE_BASES = {
    "brand_assets": "品牌资产库",
    "brand_keywords": "品牌关键词库",
    "compliance_rules": "合规红线库",
    "hit_cases": "历史爆款案例库",
}


def _split_blocks(text: str) -> list[str]:
    """按空行/标题把文档切成小块，保留有意义的片段。"""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks: list[str] = []
    for b in blocks:
        # 过长的块再按句子粗切到约 300 字
        if len(b) > 350:
            sentences = re.split(r"(?<=[。！？\n])", b)
            cur = ""
            for s in sentences:
                cur += s
                if len(cur) >= 300:
                    chunks.append(cur.strip())
                    cur = ""
            if cur.strip():
                chunks.append(cur.strip())
        else:
            chunks.append(b)
    return chunks


class KnowledgeBase:
    """单个知识库，支持 BM25 与可选向量检索。"""

    def __init__(self, dir_name: str, display_name: str) -> None:
        self.dir_name = dir_name
        self.display_name = display_name
        self.path = os.path.join(DATA_DIR, dir_name)
        self.chunks: list[str] = []
        self._bm25 = None
        self._vector_store = None
        self._load()

    def _load(self) -> None:
        if not os.path.isdir(self.path):
            return
        for fname in sorted(os.listdir(self.path)):
            if not fname.endswith((".txt", ".md")):
                continue
            with open(os.path.join(self.path, fname), encoding="utf-8") as f:
                self.chunks.extend(_split_blocks(f.read()))
        if not self.chunks:
            return
        # 优先建向量索引
        try:
            self._try_build_vector()
        except Exception:
            self._vector_store = None
        # 同时建 BM25（兜底/融合）
        self._build_bm25()

    def _tokenize(self, text: str) -> list[str]:
        # 简易中文分词：单字 + 英文词，足够 BM25 关键词匹配
        tokens = re.findall(r"[a-zA-Z0-9]+|[一-鿿]", text)
        return tokens

    def _build_bm25(self) -> None:
        from rank_bm25 import BM25Okapi

        corpus = [self._tokenize(c) for c in self.chunks]
        self._bm25 = BM25Okapi(corpus)

    def _try_build_vector(self) -> None:
        from langchain_community.vectorstores import Chroma
        from langchain_core.documents import Document

        from app.llm import get_embeddings

        embeddings = get_embeddings()
        if embeddings is None:
            return
        docs = [Document(page_content=c, metadata={"base": self.dir_name}) for c in self.chunks]
        persist_dir = os.path.join(
            os.path.dirname(DATA_DIR), "..", "chroma_db", self.dir_name
        )
        persist_dir = os.path.abspath(persist_dir)
        self._vector_store = Chroma.from_documents(
            docs, embeddings, persist_directory=persist_dir
        )

    def retrieve(self, query: str, k: int = 4) -> list[str]:
        if not self.chunks:
            return []
        scored: dict[str, float] = {}
        # 向量召回
        if self._vector_store is not None:
            for d, score in self._vector_store.similarity_search_with_relevance_scores(
                query, k=k
            ):
                scored[d.page_content] = scored.get(d.page_content, 0) + float(score)
        # BM25 召回
        if self._bm25 is not None:
            scores = self._bm25.get_scores(self._tokenize(query))
            top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            for i in top_idx:
                c = self.chunks[i]
                # BM25 分数归一化后加权
                norm = min(scores[i] / 20.0, 1.0) if scores[i] > 0 else 0
                scored[c] = scored.get(c, 0) + norm
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
        return [c for c, _ in ranked[:k]] if ranked else self.chunks[:k]

    def all_content(self) -> str:
        return "\n\n".join(self.chunks)


@lru_cache
def get_all_bases() -> dict[str, KnowledgeBase]:
    return {
        name: KnowledgeBase(name, cn_name) for name, cn_name in KNOWLEDGE_BASES.items()
    }


def query_knowledge(base_name: str, query: str, k: int = 4) -> str:
    """检索单个知识库，返回拼接文本。"""
    base = get_all_bases().get(base_name)
    if base is None:
        return ""
    hits = base.retrieve(query, k=k)
    if not hits:
        return ""
    return f"【{base.display_name}】\n" + "\n---\n".join(hits)


def query_all(query: str, k: int = 2) -> str:
    """跨四个知识库检索，返回拼接文本。"""
    parts = []
    for name in KNOWLEDGE_BASES:
        text = query_knowledge(name, query, k=k)
        if text:
            parts.append(text)
    return "\n\n".join(parts)
