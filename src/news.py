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

from src.config import COMPANY_NAMES, MARKET_NEWS_SLOTS, NEWS_PER_EVENT

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
        source = e.get("source", {}).get("title", "")
        items.append({
            "title": _clean_title(e.title, source),
            "source": source,
            "url": e.link,
            "published": published.isoformat(),
        })
    return items


def _clean_title(title: str, source: str) -> str:
    """Drop the " - Source" suffix Google adds; some outlets also repeat a
    short form of their name ("... - Suno" from "Suno - Investimentos")."""
    title = title.rsplit(" - ", 1)[0]
    head, _, tail = title.rpartition(" - ")
    if head and source.lower().startswith(tail.lower()):
        title = head
    return title


def _normalize(title: str) -> str:
    # The same story is often syndicated by several outlets with identical headlines.
    return re.sub(r"\W+", " ", title.lower()).strip()


def fetch_news(ticker: str, event: dict) -> list[dict]:
    start = date.fromisoformat(event["prev_date"])
    end = date.fromisoformat(event["date"]) + timedelta(days=1)

    # Market terms filter out noise like job openings or sponsorships
    # (tested on PETR4 2026-11-04: plain name returned "concurso Petrobras").
    queries = [f'"{COMPANY_NAMES[ticker]}" (ações OR {ticker} OR Ibovespa OR bolsa)']
    if event["scope"] == "market":
        # Market-wide move: macro context matters. Direction words rank "why the
        # market fell" articles above generic "Ibovespa hits record" pieces
        # (tested on 2025-12-05 and 2026-02-04).
        queries.append("(Ibovespa OR bolsa) (cai OR queda OR despenca OR sobe OR dispara OR alta)")

    # Market-wide move: reserve slots for Ibovespa news. Without the quota the
    # company query filled all 8 slots and the macro cause was cut off
    # (ITUB4 2026-10-26, -13.7% on election day: 5/8 headlines were about an
    # unrelated acquisition -> "no clear explanation").
    quotas = [NEWS_PER_EVENT - MARKET_NEWS_SLOTS, MARKET_NEWS_SLOTS] if len(queries) == 2 else [NEWS_PER_EVENT]

    seen, results = set(), []
    for q, quota in zip(queries, quotas):
        taken = 0
        for item in _search(q, start, end):  # Google's relevance order
            key = _normalize(item["title"])
            if key in seen or item["url"] in seen:
                continue
            seen.update({key, item["url"]})
            results.append(item)
            taken += 1
            if taken == quota:
                break
        time.sleep(1)  # be polite to an unofficial endpoint
    return results


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
