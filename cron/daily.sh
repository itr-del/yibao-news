#!/bin/bash
# 日报生成定时任务 — 北京时间每天 08:00 执行
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
mkdir -p logs
# 使用北京时间日期
DATE=$(TZ=Asia/Shanghai date +%Y-%m-%d)
exec python3 -m server.pipeline.daily_gen "$DATE" >> logs/daily.log 2>&1
