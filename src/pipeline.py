"""Step 6: end-to-end pipeline with a per-event cache.

prices -> detect -> (only NEW events) news -> Claude -> data/events/{TICKER}.json

The cache key is (ticker, date). An event already in the file is never sent to
the API again, so the daily job only pays for the day's new events and the
backfill can be stopped and resumed safely (the file is saved after each event).

Usage:
    python -m src.pipeline --dry-run   # show what would be explained, no API calls
    python -m src.pipeline             # run it
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import anthropic

from src.config import EVAL_DIR, EVENTS_DIR, MODEL, TICKERS
from src.detect import detect_events
from src.explain import explain_event
from src.news import fetch_news
from src.prices import main as download_prices

EST_COST_PER_EVENT = 0.0005  # USD, upper end of the smoke test (Haiku 5.5)


def load_cache(ticker: str) -> dict[str, dict]:
    path = EVENTS_DIR / f"{ticker}.json"
    if not path.exists():
        return {}
    return {e["date"]: e for e in json.loads(path.read_text(encoding="utf-8"))}


def save_cache(ticker: str, cache: dict[str, dict]) -> None:
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    events = sorted(cache.values(), key=lambda e: e["date"])  # site reads it in order
    (EVENTS_DIR / f"{ticker}.json").write_text(
        json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def log_run(summary: dict) -> None:
    # One JSON line per run: cost and time history for the eval section / README.
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_DIR / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="list new events, no API calls")
    parser.add_argument("--skip-prices", action="store_true", help="use prices already on disk")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not args.skip_prices:
        download_prices()

    pending = []  # (ticker, event) not in cache yet
    for ticker in TICKERS:
        cache = load_cache(ticker)
        pending += [(ticker, e) for e in detect_events(ticker) if e["date"] not in cache]

    print(f"\n{len(pending)} new events to explain "
          f"(estimated cost <= ${len(pending) * EST_COST_PER_EVENT:.3f})")
    if args.dry_run or not pending:
        for ticker, e in pending:
            print(f"  {ticker} {e['date']} {e['return']:+.2%} [{e['scope']}]")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is empty: fill it in .env (local) or GitHub Secrets (CI).")
    client = anthropic.Anthropic()

    started = time.perf_counter()
    done, failed, cost = 0, [], 0.0
    for ticker, event in pending:
        try:
            news = fetch_news(ticker, event)
            ai = explain_event(client, ticker, event, news)
        except Exception as exc:  # one bad event must not kill the run; it is retried next run
            failed.append(f"{ticker} {event['date']}: {exc}")
            print(f"  FAILED {ticker} {event['date']}: {exc}")
            continue

        cache = load_cache(ticker)
        cache[event["date"]] = {
            **event,
            "news": news,  # everything the model saw: needed for the eval and for audit
            "ai": ai,
            "explained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_cache(ticker, cache)  # save per event: a crash loses at most one call
        done += 1
        cost += ai["meta"]["cost_usd"]
        print(f"  [{done}/{len(pending)}] {ticker} {event['date']} {event['return']:+.2%} "
              f"-> {ai['type']}/{ai['confidence']}: {ai['short_reason']}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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


if __name__ == "__main__":
    main()
