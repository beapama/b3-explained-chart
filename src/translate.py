"""Step 11c: one-time English translation of the explanations already cached.

New events get English from the explain call itself. Events explained before
that are translated, not re-explained: the Portuguese text, its sources and
the evaluation labels stay exactly as they were. Only events without
``explanation_en`` are sent. ``Translation`` has no class docstring on
purpose: Pydantic would send it to the API as the schema description.

Usage:
    python -m src.translate --dry-run    Count events and estimate the cost, no API calls.
    python -m src.translate              Translate them.
"""

import argparse
import sys
import time

import anthropic
from pydantic import BaseModel, Field

from src.config import MODEL, TICKERS, require_api_key, token_cost_usd
from src.explain import NO_EXPLANATION, check_stop_reason
from src.pipeline import load_cache, log_run, now_iso, save_cache

EST_COST_PER_EVENT = 0.0003
"""USD per translation: about 400 input and 400 output tokens."""

MAX_TOKENS = 1500
EFFORT = "low"

SYSTEM_PROMPT = """You translate short Brazilian Portuguese texts about stock moves into clear, natural English for international readers.
- Keep every fact, number, ticker and name; do not add, remove or soften anything.
- Keep "Ibovespa" and company names as they are; use common English names for institutions when one exists (e.g. Banco Central -> Central Bank).
- short_reason_en: max 8 words, same meaning as the Portuguese short reason."""


class Translation(BaseModel):
    short_reason_en: str = Field(description="English short reason, max 8 words")
    explanation_en: str = Field(description="English explanation")


def translate(client: anthropic.Anthropic, ai: dict) -> tuple[dict, float]:
    """Translate one cached explanation; return the English fields and the call's cost."""
    response = client.messages.parse(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Short reason: {ai['short_reason']}\n\nExplanation: {ai['explanation']}"}
        ],
        output_format=Translation,
    )
    check_stop_reason(response, "translation")
    out: Translation = response.parsed_output
    short = NO_EXPLANATION if ai["short_reason"] == NO_EXPLANATION else out.short_reason_en
    cost = token_cost_usd(response.usage.input_tokens, response.usage.output_tokens)
    return {"short_reason_en": short, "explanation_en": out.explanation_en}, cost


def find_untranslated() -> list[tuple[str, str]]:
    """Return (ticker, date) of the cached events that have no English explanation."""
    return [(t, e["date"]) for t in TICKERS for e in load_cache(t).values() if not e["ai"].get("explanation_en")]


def run(pending: list[tuple[str, str]]) -> None:
    """Translate and save each pending event, keep going past failures, and log the run."""
    client = anthropic.Anthropic()
    started, done, failed, total = time.perf_counter(), 0, 0, 0.0
    for ticker, day in pending:
        cache = load_cache(ticker)
        try:
            fields, cost = translate(client, cache[day]["ai"])
        except Exception as exc:
            failed += 1
            print(f"  FAILED {ticker} {day}: {exc}")
            continue
        cache[day]["ai"].update(fields)
        save_cache(ticker, cache)
        done += 1
        total += cost
        print(f"  [{done}/{len(pending)}] {ticker} {day}: {fields['short_reason_en']}")

    summary = {
        "run_at": now_iso(),
        "kind": "translate",
        "model": MODEL,
        "new_events": 0,
        "translated": done,
        "failed": failed,
        "cost_usd": round(total, 5),
        "duration_s": round(time.perf_counter() - started, 1),
    }
    log_run(summary)
    print(f"\nRun summary: {summary}")


def main() -> None:
    """Parse the command line and translate the events that still lack English."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="count events, no API calls")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    pending = find_untranslated()
    print(f"{len(pending)} events to translate (estimated cost <= ${len(pending) * EST_COST_PER_EVENT:.3f})")
    if args.dry_run or not pending:
        return
    require_api_key(".env")
    run(pending)


if __name__ == "__main__":
    main()
