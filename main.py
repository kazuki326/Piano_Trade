import urllib.request
import xml.etree.ElementTree as ET
import re
from collections import Counter

# Simple list of RSS feeds to fetch
RSS_FEEDS = [
    "https://news.yahoo.co.jp/rss/topics/business.xml",
    "https://www.nikkei.com/rss/newsflash/all.xml",
]

# Mapping from keywords to stock tickers (example)
KEYWORD_STOCK_MAP = {
    "トヨタ": "7203.T",
    "ソニー": "6758.T",
    "三菱": "8058.T",
    "任天堂": "7974.T",
}

def fetch_rss(url: str) -> bytes:
    """Fetch RSS feed and return raw bytes."""
    with urllib.request.urlopen(url, timeout=10) as res:
        return res.read()

def parse_rss(data: bytes):
    """Parse RSS feed bytes and yield (title, description)."""
    root = ET.fromstring(data)
    for item in root.iter('item'):
        title = item.findtext('title', default='')
        description = item.findtext('description', default='')
        yield title, description

def extract_keywords(text: str):
    """Extract naive Japanese keywords from text."""
    pattern = re.compile(r"[\u3040-\u309F]+|[\u30A0-\u30FF]+|[\u4E00-\u9FFF]+|[A-Za-z]+")
    return pattern.findall(text)


def select_stocks_from_keywords(words):
    """Return a set of tickers based on extracted words."""
    stocks = set()
    for w in words:
        if w in KEYWORD_STOCK_MAP:
            stocks.add(KEYWORD_STOCK_MAP[w])
    return stocks


def main():
    word_counter = Counter()
    for url in RSS_FEEDS:
        try:
            data = fetch_rss(url)
            for title, desc in parse_rss(data):
                words = extract_keywords(title + ' ' + desc)
                word_counter.update(words)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

    stocks = select_stocks_from_keywords(word_counter.keys())
    print("抽出された注目株:")
    for s in sorted(stocks):
        print(s)

if __name__ == "__main__":
    main()
