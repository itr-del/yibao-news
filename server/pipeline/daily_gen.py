"""日报生成：将过去 24 小时精选条目按分类组装为日报"""
import datetime
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Item, Daily, get_session
from config import CATEGORIES, SELECTED_SCORE_THRESHOLD

logger = logging.getLogger("yibao.daily")


def generate_daily(date_str: str = None, session=None) -> str | None:
    """
    Generate a daily report for the given date (YYYY-MM-DD).
    Returns the daily ID if created, None if not enough content.
    """
    if date_str is None:
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    if session is None:
        session = get_session()

    # Check if daily already exists
    existing = session.query(Daily).filter(Daily.date == date_str).first()
    if existing:
        logger.info("Daily for %s already exists", date_str)
        return existing.id

    # Fetch items from the date (UTC)
    start = datetime.datetime.fromisoformat(f"{date_str}T00:00:00")
    end = start + datetime.timedelta(days=1)

    items = (
        session.query(Item)
        .filter(
            Item.published_at >= start,
            Item.published_at < end,
            Item.ai_selected == True,
            Item.duplicate_of_id.is_(None),
        )
        .order_by(Item.final_score.desc())
        .all()
    )

    if len(items) < 3:
        logger.info("Not enough items (%d) for daily on %s — skipping", len(items), date_str)
        return None

    # Group by category
    sections_map: dict[str, list[Item]] = {}
    for item in items:
        cat = item.category or "industry"
        if cat not in sections_map:
            sections_map[cat] = []
        sections_map[cat].append(item)

    # Build sections in CATEGORIES order (only non-empty)
    sections = []
    for cat_slug, cat_label in CATEGORIES.items():
        if cat_slug in sections_map:
            sections.append({
                "label": cat_label,
                "items": [i.id for i in sections_map[cat_slug]],
            })

    # Lead: highest-scored item
    lead_item = items[0]
    lead_title = lead_item.title_zh or lead_item.title
    lead_summary = lead_item.summary_zh or ""

    # Flashes: quick one-liners from items not in lead
    flashes = [
        (item.title_zh or item.title)[:80]
        for item in items[1:6]
    ]

    daily = Daily(
        date=date_str,
        generated_at=datetime.datetime.utcnow(),
        lead_title=lead_title,
        lead_summary=lead_summary,
        sections_json=json.dumps(sections, ensure_ascii=False),
        flashes_json=json.dumps(flashes, ensure_ascii=False),
    )
    session.add(daily)
    session.commit()

    logger.info(
        "Generated daily for %s: %d items in %d sections",
        date_str, len(items), len(sections),
    )
    return daily.id


def regenerate_recent_dailies(days: int = 7, session=None):
    """Generate or update dailies for the last N days."""
    if session is None:
        session = get_session()

    today = datetime.datetime.utcnow().date()
    created = 0
    for offset in range(days):
        date_str = (today - datetime.timedelta(days=offset)).strftime("%Y-%m-%d")
        result = generate_daily(date_str, session)
        if result:
            created += 1
    return created


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    s = get_session()
    count = regenerate_recent_dailies(7, s)
    print(f"Generated {count} dailies")
    s.close()
