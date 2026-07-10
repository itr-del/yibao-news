"""Daily API — /api/public/daily, /api/public/dailies"""
import datetime
import json
import logging

from fastapi import APIRouter, Query, HTTPException

from models import Item, Daily, get_session
from config import CATEGORIES

router = APIRouter()
logger = logging.getLogger("yibao.api.daily")


def _daily_to_dict(daily: Daily, session) -> dict:
    sections = json.loads(daily.sections_json) if daily.sections_json else []
    flashes = json.loads(daily.flashes_json) if daily.flashes_json else []

    # Resolve item IDs to full items
    resolved_sections = []
    for sec in sections:
        item_ids = sec.get("items", [])
        items = session.query(Item).filter(Item.id.in_(item_ids)).all() if item_ids else []
        item_map = {i.id: _item_to_dict(i) for i in items}
        resolved_sections.append({
            "label": sec["label"],
            "items": [item_map.get(iid) for iid in item_ids if item_map.get(iid)],
        })

    return {
        "date": daily.date,
        "generatedAt": daily.generated_at.isoformat() if daily.generated_at else None,
        "lead": {
            "title": daily.lead_title,
            "summary": daily.lead_summary,
        } if daily.lead_title else None,
        "sections": resolved_sections,
        "flashes": flashes,
    }


def _item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "titleZh": item.title_zh,
        "summaryZh": item.summary_zh,
        "url": item.url,
        "source": {"id": item.source_id, "name": item.source_name, "kind": item.source_kind},
        "publishedAt": item.published_at.isoformat() if item.published_at else None,
        "fetchedAt": item.fetched_at.isoformat() if item.fetched_at else None,
        "category": item.category,
        "tags": [],
        "aiRelevance": item.ai_relevance,
        "qualityScore": item.quality_score,
        "finalScore": item.final_score,
        "aiSelected": item.ai_selected,
        "aiSelectedReason": item.ai_selected_reason,
    }


@router.get("/api/public/daily")
def get_latest_daily():
    session = get_session()
    try:
        daily = session.query(Daily).order_by(Daily.date.desc()).first()
        if not daily:
            raise HTTPException(status_code=404, detail="no daily report yet")
        return _daily_to_dict(daily, session)
    finally:
        session.close()


@router.get("/api/public/daily/{date}")
def get_daily_by_date(date: str):
    # Validate date format
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date format must be YYYY-MM-DD")

    session = get_session()
    try:
        daily = session.query(Daily).filter(Daily.date == date).first()
        if not daily:
            raise HTTPException(status_code=404, detail=f"no daily for {date}")
        return _daily_to_dict(daily, session)
    finally:
        session.close()


@router.get("/api/public/dailies")
def list_dailies(take: int = Query(30, ge=1, le=180)):
    session = get_session()
    try:
        dailies = session.query(Daily).order_by(Daily.date.desc()).limit(take).all()
        return {
            "count": len(dailies),
            "dailies": [
                {"date": d.date, "generatedAt": d.generated_at.isoformat() if d.generated_at else None}
                for d in dailies
            ],
        }
    finally:
        session.close()
