"""
医保 HOT — 中文医保新闻 AI 资讯服务
FastAPI entry point
"""
import datetime
import json
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from models import Item, Daily, init_db, get_session
from config import CATEGORIES, PORT, HOST
from api.items import router as items_router
from api.daily import router as daily_router
from api.sources import router as sources_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="医保 HOT API",
    version="1.0.0",
    lifespan=lifespan,
    description="中文医保政策/行业新闻 AI 资讯服务，对标 AI HOT 架构",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular API routers
app.include_router(items_router)
app.include_router(daily_router)
app.include_router(sources_router)


# ── OpenAPI spec ─────────────────────────────────────────────────────────────

@app.get("/openapi.yaml", response_class=PlainTextResponse)
def openapi_yaml():
    return yaml.dump(app.openapi(), allow_unicode=True, sort_keys=False)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    from models import init_db
    init_db()
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}


# ── Admin: trigger pipeline ──────────────────────────────────────────────────

@app.post("/admin/fetch")
def admin_fetch():
    """Manually trigger fetch pipeline (for cron testing)."""
    from pipeline.fetch import fetch_all_sources
    session = get_session()
    try:
        count = fetch_all_sources(session)
        return {"status": "ok", "fetched": count}
    finally:
        session.close()


@app.post("/admin/process")
def admin_process():
    """Manually trigger AI processing pipeline."""
    from pipeline.ai_process import process_unprocessed_items
    session = get_session()
    try:
        count = process_unprocessed_items(session)
        return {"status": "ok", "processed": count}
    finally:
        session.close()


@app.post("/admin/daily/{date}")
def admin_daily(date: str):
    """Generate daily report for a specific date."""
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date format must be YYYY-MM-DD")

    from pipeline.daily_gen import generate_daily
    session = get_session()
    try:
        result = generate_daily(date, session)
        if result:
            return {"status": "ok", "daily_id": result, "date": date}
        return {"status": "skipped", "reason": "not enough items", "date": date}
    finally:
        session.close()


@app.post("/admin/daily/regenerate")
def admin_regenerate(days: int = Query(7, ge=1, le=30)):
    """Regenerate dailies for the last N days."""
    from pipeline.daily_gen import regenerate_recent_dailies
    session = get_session()
    try:
        count = regenerate_recent_dailies(days, session)
        return {"status": "ok", "created": count, "days": days}
    finally:
        session.close()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
