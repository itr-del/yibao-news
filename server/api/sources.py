"""Sources API — /api/public/sources"""
import logging

from fastapi import APIRouter

from config import RSS_SOURCES, CATEGORIES

router = APIRouter()
logger = logging.getLogger("yibao.api.sources")


@router.get("/api/public/sources")
def get_sources():
    enabled_sources = [s for s in RSS_SOURCES if s.get("enabled")]
    return {
        "count": len(enabled_sources),
        "sources": enabled_sources,
    }


@router.get("/api/public/categories")
def get_categories():
    """Return category list for frontend consumption."""
    return {
        "categories": [
            {"slug": k, "label": v}
            for k, v in CATEGORIES.items()
        ]
    }
