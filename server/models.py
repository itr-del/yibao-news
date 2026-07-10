import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Index, create_engine
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import DB_PATH, CATEGORIES
import os


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, default=lambda: f"yb_{uuid.uuid4().hex[:16]}")
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    title_zh = Column(String, nullable=True)
    summary_zh = Column(Text, nullable=True)

    # Source
    source_id = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_kind = Column(String, nullable=False)  # rss / scraper / manual

    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Category (one of CATEGORIES keys)
    category = Column(String, nullable=True)

    # AI tags (JSON array stored as string)
    tags = Column(Text, nullable=True)  # JSON array: ["tag1","tag2"]

    # AI scores
    ai_relevance = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    final_score = Column(Integer, nullable=True)

    # Selection
    ai_selected = Column(Boolean, default=False)
    ai_selected_reason = Column(Text, nullable=True)

    # Processing state
    ai_processed = Column(Boolean, default=False)
    ai_processed_at = Column(DateTime, nullable=True)

    # Dedup
    duplicate_of_id = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_items_url", "url", unique=True),
        Index("idx_items_published_at", "published_at"),
        Index("idx_items_selected", "ai_selected"),
        Index("idx_items_category", "category"),
        Index("idx_items_source", "source_id"),
    )


class Daily(Base):
    __tablename__ = "dailies"

    id = Column(String, primary_key=True, default=lambda: f"dl_{uuid.uuid4().hex[:16]}")
    date = Column(String, nullable=False, unique=True)  # YYYY-MM-DD
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    lead_title = Column(String, nullable=True)
    lead_summary = Column(Text, nullable=True)
    sections_json = Column(Text, nullable=True)  # JSON: [{label, items:[id,...]}]
    flashes_json = Column(Text, nullable=True)  # JSON: [title1, title2, ...]


def init_db(db_path: str = None):
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = None):
    path = db_path or DB_PATH
    engine = create_engine(f"sqlite:///{path}")
    Session = sessionmaker(bind=engine)
    return Session()
