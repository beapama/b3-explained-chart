"""Step 4: fetch the headlines around an event from Google News RSS.

Free, no key, and it supports date filters through the ``after:`` and
``before:`` search operators. The window runs from the previous trading day to
the day after the event: it covers overnight and weekend news and the
same-evening "why it moved" articles.

Query choices, each tested on real events:

* Company query: name plus market terms. The plain name returned job
  contests and sponsorships (PETR4 on 2026-11-04).
* Market query, only on market-wide moves: direction words rank "why the
  market fell" articles above generic "Ibovespa hits a record" pieces
  (2025-12-05 and 2026-02-04).
* Market-wide moves reserve ``MARKET_NEWS_SLOTS`` for the market query.
  Without the quota the company news filled every slot and the macro cause
  was cut (ITUB4, -13.7% on election day, got five headlines about an
  unrelated acquisition).

Usage:
    python -m src.news
"""

import re
import sys
import time
from datetime import UTC, date, datetime, timedelta
from urllib.parse import quote

import feedparser

from src.config import COMPANY_NAMES, MARKET_NEWS_SLOTS, NEWS_PER_EVENT

RSS_URL = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
MARKET_QUERY = "(Ibovespa OR bolsa) (cai OR queda OR despenca OR sobe OR dispara OR alta)"
REQUEST_DELAY_S = 1
SOURCE_SEPARATOR = " - "


def company_query(ticker: str) -> str:
    """Return the search query for a company's own news."""
    return f'"{COMPANY_NAMES[ticker]}" (ações OR {ticker} OR Ibovespa OR bolsa)'


def _search(query: str, start: date, end: date) -> list[dict]:
    """Return the headlines for ``query`` published between ``start`` and ``end``, inclusive.

    Google's ``after:`` and ``before:`` are exclusive and approximate, so the
    request is widened by a day and the result filtered on the published date.
    """
    q = f"{query} after:{start - timedelta(days=1)} before:{end + timedelta(days=1)}"
    feed = feedparser.parse(RSS_URL.format(q=quote(q)))
    items = []
    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=UTC).date()
        if not start <= published <= end:
            continue
        source = entry.get("source", {}).get("title", "")
        items.append(
            {
                "title": _clean_title(entry.title, source),
                "source": source,
                "url": entry.link,
                "published": published.isoformat(),
            }
        )
    return items


def _clean_title(title: str, source: str) -> str:
    """Drop the " - Source" suffix Google adds, and a repeated short source name ("... - Suno")."""
    title = title.rsplit(SOURCE_SEPARATOR, 1)[0]
    head, _, tail = title.rpartition(SOURCE_SEPARATOR)
    if head and source.lower().startswith(tail.lower()):
        title = head
    return title


def _normalize(title: str) -> str:
    """Return a comparison key for a headline; syndicated stories repeat the same title."""
    return re.sub(r"\W+", " ", title.lower()).strip()


def _queries_with_quotas(ticker: str, scope: str) -> list[tuple[str, int]]:
    """Return each query with the number of headlines it may contribute."""
    if scope == "market":
        return [(company_query(ticker), NEWS_PER_EVENT - MARKET_NEWS_SLOTS), (MARKET_QUERY, MARKET_NEWS_SLOTS)]
    return [(company_query(ticker), NEWS_PER_EVENT)]


def fetch_news(ticker: str, event: dict) -> list[dict]:
    """Return up to ``NEWS_PER_EVENT`` deduplicated headlines for an event, in Google's relevance order."""
    start = date.fromisoformat(event["prev_date"])
    end = date.fromisoformat(event["date"]) + timedelta(days=1)

    seen, results = set(), []
    for query, quota in _queries_with_quotas(ticker, event["scope"]):
        taken = 0
        for item in _search(query, start, end):
            key = _normalize(item["title"])
            if key in seen or item["url"] in seen:
                continue
            seen.update({key, item["url"]})
            results.append(item)
            taken += 1
            if taken == quota:
                break
        time.sleep(REQUEST_DELAY_S)
    return results


def main() -> None:
    """Print the headlines found for three known events."""
    from src.detect import detect_events

    sys.stdout.reconfigure(encoding="utf-8")
    samples = [("MGLU3", "2026-10-26"), ("PETR4", "2026-11-04"), ("WEGE3", "2026-10-21")]
    for ticker, day in samples:
        event = next(e for e in detect_events(ticker) if e["date"] == day)
        news = fetch_news(ticker, event)
        print(f"\n{ticker} {day} ({event['return']:+.2%}, {event['scope']}): {len(news)} articles")
        for n in news:
            print(f"  [{n['published']}] {n['source']}: {n['title'][:110]}")


if __name__ == "__main__":
    main()
