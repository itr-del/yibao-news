"""去重模块 — URL精确去重 + 标题相似度去重"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from difflib import SequenceMatcher
from models import Item, get_session

logger = logging.getLogger("yibao.dedup")

TITLE_SIMILARITY_THRESHOLD = 0.85  # Mark as duplicate if title similarity exceeds this


def dedup_by_url(session=None) -> int:
    """Remove exact URL duplicates (keep first). Returns count removed."""
    if session is None:
        session = get_session()

    # Find duplicate URLs
    from sqlalchemy import func
    dupes = (
        session.query(Item.url, func.count(Item.id).label("cnt"))
        .group_by(Item.url)
        .having(func.count(Item.id) > 1)
        .all()
    )

    removed = 0
    for url, _ in dupes:
        items = session.query(Item).filter(Item.url == url).order_by(Item.fetched_at.asc()).all()
        keeper = items[0]
        for dup in items[1:]:
            dup.duplicate_of_id = keeper.id
            session.add(dup)
            removed += 1

    if removed:
        session.commit()
        logger.info("URL dedup: marked %d duplicates", removed)
    return removed


def dedup_by_title_similarity(session=None) -> int:
    """Mark near-duplicate titles as duplicates. Returns count marked."""
    if session is None:
        session = get_session()

    # Get unprocessed items from last 3 days
    import datetime
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    items = (
        session.query(Item)
        .filter(Item.published_at >= cutoff, Item.duplicate_of_id.is_(None))
        .order_by(Item.published_at.asc())
        .all()
    )

    removed = 0
    for i, item_a in enumerate(items):
        if item_a.duplicate_of_id:
            continue
        for item_b in items[i + 1:]:
            if item_b.duplicate_of_id:
                continue
            sim = SequenceMatcher(None, item_a.title, item_b.title).ratio()
            if sim >= TITLE_SIMILARITY_THRESHOLD:
                item_b.duplicate_of_id = item_a.id
                session.add(item_b)
                removed += 1

    if removed:
        session.commit()
        logger.info("Title dedup: marked %d duplicates", removed)
    return removed


def run_dedup(session=None):
    if session is None:
        session = get_session()
    a = dedup_by_url(session)
    b = dedup_by_title_similarity(session)
    return a + b


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    s = get_session()
    count = run_dedup(s)
    print(f"Dedup complete: {count} duplicates marked")
    s.close()
