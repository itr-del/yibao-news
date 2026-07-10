"""RSS/网页采集模块 — 增强版，适配国家医保局等政务网站"""
import datetime
import hashlib
import logging
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

import feedparser
import requests
from bs4 import BeautifulSoup
from models import Item, get_session

logger = logging.getLogger("yibao.fetch")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# NHSA article list page selectors
NHSA_SELECTORS = {
    "dynamic": {
        "url": "http://www.nhsa.gov.cn/col/col14/index.html",
        "link_selector": "div.list li a",
        "title_attr": "title",
        "url_attr": "href",
        "base_url": "http://www.nhsa.gov.cn",
    },
    "policy": {
        "url": "http://www.nhsa.gov.cn/col/col104/index.html",
        "link_selector": "div.list li a",
        "title_attr": "title",
        "url_attr": "href",
        "base_url": "http://www.nhsa.gov.cn",
    },
    "data": {
        "url": "http://www.nhsa.gov.cn/col/col7/index.html",
        "link_selector": "div.list li a",
        "title_attr": "title",
        "url_attr": "href",
        "base_url": "http://www.nhsa.gov.cn",
    },
}


def fetch_rss(source: dict) -> list[dict]:
    """Fetch items from an RSS source. Returns list of raw item dicts."""
    rss_url = source.get("rss_url")
    if not rss_url:
        logger.info("No RSS URL for source %s, skipping RSS", source["id"])
        return []

    try:
        resp = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        items = []
        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime.datetime(*entry.updated_parsed[:6])

            items.append({
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "summary_raw": entry.get("summary", ""),
                "published_at": published,
                "source_id": source["id"],
                "source_name": source["name"],
                "source_kind": "rss",
            })
        logger.info("Fetched %d items from RSS %s", len(items), source["id"])
        return items
    except Exception as e:
        logger.error("Error fetching RSS from %s: %s", source["id"], e)
        return []


def fetch_nhsa_section(source: dict, section_key: str) -> list[dict]:
    """Fetch article links from a specific NHSA section page."""
    selector = NHSA_SELECTORS.get(section_key)
    if not selector:
        return []

    try:
        resp = requests.get(selector["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        items = []
        for link in soup.select(selector["link_selector"]):
            href = link.get(selector["url_attr"], "")
            title = link.get(selector["title_attr"], "")

            if not href or not title:
                continue

            # Resolve relative URLs
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(selector["base_url"], href)
            elif not href.startswith("http"):
                continue

            # Skip non-article links
            if not re.search(r'/art/\d+/', href):
                continue

            # Clean title
            title = title.strip()
            if len(title) < 5:
                continue

            items.append({
                "url": href,
                "title": title,
                "summary_raw": "",
                "published_at": None,
                "source_id": source["id"],
                "source_name": source["name"],
                "source_kind": "scraper",
            })

        logger.info("Fetched %d articles from NHSA %s", len(items), section_key)
        return items
    except Exception as e:
        logger.error("Error fetching NHSA section %s: %s", section_key, e)
        return []


def fetch_scraper(source: dict) -> list[dict]:
    """Scrape items from a web page. Enhanced implementation."""
    url = source.get("url")
    if not url:
        return []

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        items = []
        # Try multiple common list patterns for government sites
        selectors = [
            "div.list li a",           # NHSA style
            "div.news-list li a",       # Common news list
            "ul.list li a",             # Generic list
            "div.articles a",           # Article links
            "div.content a",            # Content links
        ]

        found_links = False
        for sel in selectors:
            links = soup.select(sel)
            if links:
                found_links = True
                break

        if not found_links:
            # Fallback: find all links with reasonable text
            links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if not href or not text:
                continue

            # Filter out trivial links
            if len(text) < 8:
                continue

            # Resolve relative URLs
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            if not href.startswith("http"):
                continue

            # Only include article-like pages (skip main site navigation)
            if re.search(r'/art/\d+/', href) or re.search(r'/col/\d+/', href):
                items.append({
                    "url": href,
                    "title": text,
                    "summary_raw": "",
                    "published_at": datetime.datetime.utcnow(),
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "source_kind": "scraper",
                })

        # Limit to avoid noise
        result = items[:50]
        logger.info("Scraped %d articles from %s (total found: %d)", len(result), source["id"], len(items))
        return result
    except Exception as e:
        logger.error("Error scraping %s: %s", source["id"], e)
        return []


def fetch_all_sources(session=None):
    """Fetch from all enabled sources and save new items. Returns count of new items."""
    from config import RSS_SOURCES

    if session is None:
        session = get_session()

    all_raw = []
    for source in RSS_SOURCES:
        if not source.get("enabled"):
            continue

        if source.get("rss_url"):
            all_raw.extend(fetch_rss(source))
        elif source["id"].startswith("nhsa-"):
            # NHSA-specific: use section-based fetching
            section_key = source["id"].replace("nhsa-", "")
            if section_key == "gov":
                section_key = "dynamic"
            all_raw.extend(fetch_nhsa_section(source, section_key))
        else:
            all_raw.extend(fetch_scraper(source))

    return save_new_items(all_raw, session)


def save_new_items(items: list[dict], session=None) -> int:
    """Save new items to DB, skipping duplicates by URL. Returns count of new items."""
    if session is None:
        session = get_session()

    new_count = 0
    for raw in items:
        if not raw.get("url") or not raw.get("title"):
            continue

        existing = session.query(Item).filter(Item.url == raw["url"]).first()
        if existing:
            continue

        item = Item(
            url=raw["url"],
            title=raw["title"],
            source_id=raw["source_id"],
            source_name=raw["source_name"],
            source_kind=raw["source_kind"],
            published_at=raw.get("published_at") or datetime.datetime.utcnow(),
            fetched_at=datetime.datetime.utcnow(),
        )
        session.add(item)
        new_count += 1

    session.commit()
    logger.info("Saved %d new items", new_count)
    return new_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    session = get_session()
    count = fetch_all_sources(session)
    print(f"Fetched {count} new items")
    session.close()
