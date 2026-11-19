"""Step 4: fetch news for an event date from Google News RSS.

Free, no API key, and supports date filters via the `after:`/`before:`
search operators. Window = from the previous trading day to the day after the
event: covers overnight/weekend news and same-evening "why it moved" articles.
"""
import re
import time
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import feedparser

from src.config import COMPANY_NAMES, NEWS_PER_EVENT

RSS_URL = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _search(query: str, start: date, end: date) -> list[dict]:
    # Google's after/before are exclusive and approximate: widen by a day here
    # and filter precisely on the published date below.
    q = f"{query} after:{start - timedelta(days=1)} before:{end + timedelta(days=1)}"
    feed = feedparser.parse(RSS_URL.format(q=quote(q)))
    items = []
    for e in feed.entries:
        published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).date()
        if not start <= published <= end:
            continue
        items.append({
            "title": e.title.rsplit(" - ", 1)[0],  # drop " - Source" suffix
            "source": e.get("source", {}).get("title", ""),
            "url": e.link,
            "published": published.isoformat(),
        })
    return items


def _normalize(title: str) -> str:
    # The same story is often syndicated by several outlets with identical
    # headlines; some outlets repeat their name (" - Suno"), so drop it again.
    title = title.rsplit(" - ", 1)[0]
    return re.sub(r"\W+", " ", title.lower()).strip()


def fetch_news(ticker: str, event: dict) -> list[dict]:
    start = date.fromisoformat(event["prev_date"])
    end = date.fromisoformat(event["date"]) + timedelta(days=1)

    # Market terms filter out noise like job openings or sponsorships
    # (tested on PETR4 2026-11-04: plain name returned "concurso Petrobras").
    queries = [f'"{COMPANY_NAMES[ticker]}" (ações OR {ticker} OR Ibovespa OR bolsa)']
    if event["scope"] == "market":
        queries.append("Ibovespa")  # market-wide move: macro context matters

    seen, results = set(), []
    for q in queries:
        for item in _search(q, start, end):
            key = _normalize(item["title"])
            if key in seen or item["url"] in seen:
                continue
            seen.update({key, item["url"]})
            results.append(item)
        time.sleep(1)  # be polite to an unofficial endpoint

    # Google's relevance order; company news come before Ibovespa news.
    return results[:NEWS_PER_EVENT]


def main() -> None:
    import sys

    from src.detect import detect_events

    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    samples = [("MGLU3", "2026-10-26"), ("PETR4", "2026-11-04"), ("WEGE3", "2026-10-21")]
    for ticker, day in samples:
        event = next(e for e in detect_events(ticker) if e["date"] == day)
        news = fetch_news(ticker, event)
        print(f"\n{ticker} {day} ({event['return']:+.2%}, {event['scope']}): {len(news)} articles")
        for n in news:
            print(f"  [{n['published']}] {n['source']}: {n['title'][:110]}")


if __name__ == "__main__":
    main()
