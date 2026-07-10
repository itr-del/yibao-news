#!/bin/bash
# 采集定时任务 — 每 30 分钟执行一次（北京时间）
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
mkdir -p logs
exec python3 -m server.pipeline.fetch >> logs/fetch.log 2>&1
