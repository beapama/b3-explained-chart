"""Step 11c: one-time English translation of the explanations already cached.

New events get English from the explain call itself (src/explain.py). For the
events explained before that, we TRANSLATE the stored Portuguese text instead
of re-explaining: the Portuguese explanation, its sources and the eval labels
stay exactly as they were. Only events without `explanation_en` are sent.

Usage:
    python -m src.translate --dry-run   # count events and estimate cost, no API calls
    python -m src.translate
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone

import anthropic
from pydantic import BaseModel, Field

from src.config import MODEL, PRICE_PER_MTOK, TICKERS
from src.explain import NO_EXPLANATION
from src.pipeline import load_cache, log_run, save_cache

EST_COST_PER_EVENT = 0.0003  # USD: ~400 input + ~400 output tokens on Haiku 5.5

SYSTEM_PROMPT = """You translate short Brazilian Portuguese texts about stock moves into clear, natural English for international readers.
- Keep every fact, number, ticker and name; do not add, remove or soften anything.
- Keep "Ibovespa" and company names as they are; use common English names for institutions when one exists (e.g. Banco Central -> Central Bank).
- short_reason_en: max 8 words, same meaning as the Portuguese short reason."""


class Translation(BaseModel):
    short_reason_en: str = Field(description="English short reason, max 8 words")
    explanation_en: str = Field(description="English explanation")


def translate(client: anthropic.Anthropic, ai: dict) -> tuple[dict, float]:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=1500,
        output_config={"effort": "low"},  # plain translation, no reasoning needed
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
                   f"Short reason: {ai['short_reason']}\n\nExplanation: {ai['explanation']}"}],
        output_format=Translation,
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"stop_reason={response.stop_reason}")
    out: Translation = response.parsed_output
    u = response.usage
    cost = (u.input_tokens * PRICE_PER_MTOK["input"] + u.output_tokens * PRICE_PER_MTOK["output"]) / 1_000_000
    short = NO_EXPLANATION if ai["short_reason"] == NO_EXPLANATION else out.short_reason_en
    return {"short_reason_en": short, "explanation_en": out.explanation_en}, cost


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="count events, no API calls")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    pending = [(t, e["date"]) for t in TICKERS for e in load_cache(t).values()
               if not e["ai"].get("explanation_en")]
    print(f"{len(pending)} events to translate (estimated cost <= ${len(pending) * EST_COST_PER_EVENT:.3f})")
    if args.dry_run or not pending:
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is empty: fill it in .env.")

    client = anthropic.Anthropic()
    started, done, failed, total = time.perf_counter(), 0, 0, 0.0
    for ticker, day in pending:
        cache = load_cache(ticker)
        try:
            fields, cost = translate(client, cache[day]["ai"])
        except Exception as exc:  # keep going; a rerun picks up what is missing
            failed += 1
            print(f"  FAILED {ticker} {day}: {exc}")
            continue
        cache[day]["ai"].update(fields)
        save_cache(ticker, cache)  # save per event, like the pipeline
        done += 1
        total += cost
        print(f"  [{done}/{len(pending)}] {ticker} {day}: {fields['short_reason_en']}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "translate",
        "model": MODEL,
        "new_events": 0,  # nothing was explained; keeps cost-per-explanation honest
        "translated": done,
        "failed": failed,
        "cost_usd": round(total, 5),
        "duration_s": round(time.perf_counter() - started, 1),
    }
    log_run(summary)
    print(f"\nRun summary: {summary}")


if __name__ == "__main__":
    main()
