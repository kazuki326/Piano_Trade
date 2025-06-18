from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import feedparser
import pytest

from collector.fetch_rss import fetch_rss


def test_fetch_rss(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    feeds_file = tmp_path / "feeds.yaml"
    feeds_file.write_text("- url: http://example.com/rss\n  source: example\n")

    def fake_parse(url: str):
        assert url == "http://example.com/rss"
        return SimpleNamespace(entries=[
            SimpleNamespace(link="http://example.com/a", title="A", published="Tue, 01 Jan 2024 00:00:00 GMT"),
        ])

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    db_path = tmp_path / "raw.db"
    fetch_rss(feeds_path=feeds_file, db_path=db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT url, title, source FROM articles").fetchone()
    assert row == ("http://example.com/a", "A", "example")
