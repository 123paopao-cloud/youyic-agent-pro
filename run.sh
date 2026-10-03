#!/usr/bin/env bash
# 一键启动：FastAPI 后端 + Streamlit 前端
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "未找到 .env，正在从 .env.example 复制，请先填入 ARK_API_KEY 后重新运行。"
  cp .env.example .env
  exit 1
fi

echo "启动 FastAPI 后端（端口 8000）..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!
echo "后端 PID: $API_PID"

sleep 3
echo "启动 Streamlit 前端..."
export API_BASE_URL=http://localhost:8000
streamlit run streamlit_app.py --server.headless true

# 前端退出后顺带关闭后端
kill $API_PID 2>/dev/null
