from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl
from readability import Document
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ArticleHtml(BaseModel):
    id: int
    url: HttpUrl
    html_saved_at: datetime
    text: str | None = None
    author: str | None = None


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles(
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            html_saved_at TEXT,
            text TEXT,
            author TEXT
        )
        """
    )
    conn.commit()


def _get_pending(raw_conn: sqlite3.Connection, html_conn: sqlite3.Connection) -> Iterable[Tuple[int, str]]:
    existing = {row[0] for row in html_conn.execute("SELECT id FROM articles")}
    for row in raw_conn.execute("SELECT id, url FROM articles"):
        if row[0] not in existing:
            yield row


def _upsert(conn: sqlite3.Connection, art: ArticleHtml) -> None:
    conn.execute(
        """
        INSERT INTO articles(id, url, html_saved_at, text, author)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            url=excluded.url,
            html_saved_at=excluded.html_saved_at,
            text=excluded.text,
            author=excluded.author
        """,
        (
            art.id,
            art.url,
            art.html_saved_at.isoformat(),
            art.text,
            art.author,
        ),
    )


async def _fetch_one(browser, article_id: int, url: str) -> ArticleHtml | None:
    for attempt in range(3):
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, timeout=10000)
            try:
                await page.wait_for_selector("article", timeout=5000)
            except Exception:
                pass
            html = await page.content()
            await page.close()
            await context.close()

            doc = Document(html)
            summary = doc.summary()
            soup = BeautifulSoup(summary, "lxml")
            text = soup.get_text(separator="\n")
            author = None
            meta = soup.find("meta", attrs={"name": "author"})
            if meta:
                author = meta.get("content")
            return ArticleHtml(
                id=article_id,
                url=url,
                html_saved_at=datetime.utcnow(),
                text=text,
                author=author,
            )
        except Exception as exc:
            wait = 2 ** attempt
            logger.warning("retry %s for %s due to %s", attempt + 1, url, exc)
            await asyncio.sleep(wait)
    logger.error("failed to fetch %s", url)
    return None


async def fetch_html(
    raw_db: Path = Path("data/raw_articles.db"),
    html_db: Path = Path("data/html_articles.db"),
) -> None:
    raw_conn = sqlite3.connect(raw_db)
    html_conn = sqlite3.connect(html_db)
    _init_db(html_conn)

    targets = list(_get_pending(raw_conn, html_conn))
    if not targets:
        logger.info("no articles to fetch")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(5)

        async def worker(t: Tuple[int, str]):
            async with sem:
                art = await _fetch_one(browser, t[0], t[1])
                if art:
                    _upsert(html_conn, art)
                    html_conn.commit()

        await asyncio.gather(*(worker(t) for t in targets))
        await browser.close()

    raw_conn.close()
    html_conn.close()


def main() -> None:
    asyncio.run(fetch_html())


if __name__ == "__main__":
    main()
