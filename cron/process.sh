#!/bin/bash
# AI 处理定时任务 — 每 30 分钟执行一次
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
mkdir -p logs
exec python3 -m server.pipeline.ai_process >> logs/process.log 2>&1
