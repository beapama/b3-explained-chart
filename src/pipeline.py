"""Step 6: end-to-end pipeline with a per-event cache.

prices -> detection -> (new events only) news -> Claude -> ``data/events/{TICKER}.json``

The cache key is (ticker, date): an event already in the file is never sent to
the API again, so the daily job pays only for new events. Each event is saved
as soon as it is explained, so the backfill can stop and resume safely, and a
failed event is retried on the next run. The headlines the model saw are
stored with its answer, for auditing and for the evaluation.

Usage:
    python -m src.pipeline --dry-run    List new events and the estimated cost, no API calls.
    python -m src.pipeline              Explain the new events and cache them.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime

import anthropic

from src.config import EVAL_DIR, EVENTS_DIR, MODEL, TICKERS, require_api_key
from src.detect import detect_events
from src.explain import explain_event
from src.news import fetch_news
from src.prices import download_all

EST_COST_PER_EVENT = 0.0005
"""USD per explanation, the upper end measured in the smoke test."""

RUNS_LOG = EVAL_DIR / "runs.jsonl"


def now_iso() -> str:
    """Return the current UTC time as an ISO string with seconds."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_cache(ticker: str) -> dict[str, dict]:
    """Return the cached events of ``ticker`` keyed by date."""
    path = EVENTS_DIR / f"{ticker}.json"
    if not path.exists():
        return {}
    return {e["date"]: e for e in json.loads(path.read_text(encoding="utf-8"))}


def save_cache(ticker: str, cache: dict[str, dict]) -> None:
    """Write the events of ``ticker`` sorted by date, the order the site reads them in."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    events = sorted(cache.values(), key=lambda e: e["date"])
    (EVENTS_DIR / f"{ticker}.json").write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")


def log_run(summary: dict) -> None:
    """Append one JSON line per run to the cost and duration history."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")


def find_pending() -> list[tuple[str, dict]]:
    """Return the detected events that are not in the cache yet."""
    pending = []
    for ticker in TICKERS:
        cache = load_cache(ticker)
        pending += [(ticker, e) for e in detect_events(ticker) if e["date"] not in cache]
    return pending


def explain_and_cache(client: anthropic.Anthropic, ticker: str, event: dict) -> dict:
    """Fetch the news, explain the event, save it to the cache and return the AI record."""
    news = fetch_news(ticker, event)
    ai = explain_event(client, ticker, event, news)
    cache = load_cache(ticker)
    cache[event["date"]] = {**event, "news": news, "ai": ai, "explained_at": now_iso()}
    save_cache(ticker, cache)
    return ai


def run(pending: list[tuple[str, dict]]) -> None:
    """Explain every pending event, keep going past failures, and log the run."""
    client = anthropic.Anthropic()
    started = time.perf_counter()
    done, failed, cost = 0, [], 0.0
    for ticker, event in pending:
        try:
            ai = explain_and_cache(client, ticker, event)
        except Exception as exc:
            failed.append(f"{ticker} {event['date']}: {exc}")
            print(f"  FAILED {ticker} {event['date']}: {exc}")
            continue
        done += 1
        cost += ai["meta"]["cost_usd"]
        print(
            f"  [{done}/{len(pending)}] {ticker} {event['date']} {event['return']:+.2%} "
            f"-> {ai['type']}/{ai['confidence']}: {ai['short_reason']}"
        )

    summary = {
        "run_at": now_iso(),
        "kind": "explain",
        "model": MODEL,
        "new_events": done,
        "failed": len(failed),
        "cost_usd": round(cost, 5),
        "duration_s": round(time.perf_counter() - started, 1),
    }
    log_run(summary)
    print(f"\nRun summary: {summary}")
    if failed:
        print("Failures (will be retried next run):\n  " + "\n  ".join(failed))


def main() -> None:
    """Parse the command line, find new events and explain them (or only list them)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="list new events, no API calls")
    parser.add_argument("--skip-prices", action="store_true", help="use prices already on disk")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not args.skip_prices:
        download_all()
    pending = find_pending()
    print(f"\n{len(pending)} new events to explain (estimated cost <= ${len(pending) * EST_COST_PER_EVENT:.3f})")
    if args.dry_run or not pending:
        for ticker, e in pending:
            print(f"  {ticker} {e['date']} {e['return']:+.2%} [{e['scope']}]")
        return
    require_api_key(".env (local) or GitHub Secrets (CI)")
    run(pending)


if __name__ == "__main__":
    main()
