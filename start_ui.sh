#!/usr/bin/env bash
# 只启动前端（直连模式，最省事，部署到云端也是这个）
set -e
cd "$(dirname "$0")"
unset API_BASE_URL
streamlit run streamlit_app.py --server.headless true
