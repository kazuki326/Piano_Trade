from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import feedparser
import yaml
from pydantic import BaseModel, HttpUrl


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ArticleRaw(BaseModel):
    id: int | None = None
    url: HttpUrl
    title: str
    published: datetime | None = None
    source: str
    fetched_at: datetime


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            published TEXT,
            source TEXT,
            fetched_at TEXT
        )
        """
    )
    conn.commit()


def _upsert(conn: sqlite3.Connection, article: ArticleRaw) -> None:
    conn.execute(
        """
        INSERT INTO articles(url, title, published, source, fetched_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            published=excluded.published,
            source=excluded.source,
            fetched_at=excluded.fetched_at
        """,
        (
            article.url,
            article.title,
            article.published.isoformat() if article.published else None,
            article.source,
            article.fetched_at.isoformat(),
        ),
    )


def _parse_datetime(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime(*feedparser._parse_date(text)[:6])
    except Exception:
        return None


def fetch_rss(*, feeds_path: Path = Path("feeds.yaml"), db_path: Path = Path("data/raw_articles.db")) -> None:
    feeds: List[dict] = []
    try:
        feeds = yaml.safe_load(feeds_path.read_text()) or []
    except FileNotFoundError:
        logger.error("feeds.yaml not found: %s", feeds_path)
        return

    conn = sqlite3.connect(db_path)
    _init_db(conn)

    for feed in feeds:
        url = feed.get("url")
        source = feed.get("source", "unknown")
        if not url:
            continue
        logger.info("fetching %s", url)
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            try:
                article = ArticleRaw(
                    url=entry.link,
                    title=entry.title,
                    published=_parse_datetime(getattr(entry, "published", None)),
                    source=source,
                    fetched_at=datetime.utcnow(),
                )
                _upsert(conn, article)
            except Exception as exc:
                logger.exception("failed to process entry %s: %s", entry.get("link"), exc)
    conn.commit()
    conn.close()


def main() -> None:
    fetch_rss()


if __name__ == "__main__":
    main()
