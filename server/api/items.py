"""Items API — /api/public/items"""
import datetime
import json
import logging

from fastapi import APIRouter, Query, HTTPException

from models import Item, get_session
from config import CATEGORIES

router = APIRouter()
logger = logging.getLogger("yibao.api.items")


def _parse_tags(tags_str: str | None) -> list[str]:
    if not tags_str:
        return []
    try:
        return json.loads(tags_str)
    except (json.JSONDecodeError, TypeError):
        return []


def _item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "titleZh": item.title_zh,
        "summaryZh": item.summary_zh,
        "url": item.url,
        "source": {
            "id": item.source_id,
            "name": item.source_name,
            "kind": item.source_kind,
        },
        "publishedAt": item.published_at.isoformat() if item.published_at else None,
        "fetchedAt": item.fetched_at.isoformat() if item.fetched_at else None,
        "category": item.category,
        "tags": _parse_tags(item.tags),
        "aiRelevance": item.ai_relevance,
        "qualityScore": item.quality_score,
        "finalScore": item.final_score,
        "aiSelected": item.ai_selected,
        "aiSelectedReason": item.ai_selected_reason,
    }


@router.get("/api/public/items")
def get_items(
    mode: str = Query("selected", pattern="^(selected|all)$"),
    category: str | None = None,
    q: str | None = None,
    since: str | None = None,
    take: int = Query(50, ge=1, le=100),
    cursor: str | None = None,
):
    session = get_session()
    try:
        query = session.query(Item).filter(Item.duplicate_of_id.is_(None))

        # Mode filter
        if mode == "selected":
            query = query.filter(Item.ai_selected == True)

        # Category filter
        if category and category in CATEGORIES:
            query = query.filter(Item.category == category)

        # Since filter (default 7 days)
        if since:
            try:
                since_dt = datetime.datetime.fromisoformat(since)
                query = query.filter(Item.published_at >= since_dt)
            except (ValueError, TypeError):
                pass
        else:
            default_since = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            query = query.filter(Item.published_at >= default_since)

        # Keyword search in title + summary
        if q and q.strip():
            keyword = f"%{q.strip()}%"
            query = query.filter(
                (Item.title.like(keyword))
                | (Item.summary_zh.like(keyword))
                | (Item.title_zh.like(keyword))
            )

        # Cursor-based pagination
        if cursor:
            try:
                cursor_dt = datetime.datetime.fromisoformat(cursor)
                query = query.filter(Item.published_at < cursor_dt)
            except (ValueError, TypeError):
                pass

        # Order by published_at desc
        query = query.order_by(Item.published_at.desc())

        # Fetch +1 to detect hasNext
        total = query.count()
        items = query.limit(take + 1).all()
        has_next = len(items) > take
        if has_next:
            items = items[:take]

        next_cursor = None
        if has_next and items:
            next_cursor = items[-1].published_at.isoformat()

        return {
            "count": len(items),
            "hasNext": has_next,
            "nextCursor": next_cursor,
            "total": total,
            "items": [_item_to_dict(i) for i in items],
        }
    finally:
        session.close()
