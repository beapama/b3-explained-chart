"""Step 5: ask Claude to explain a strong move using ONLY the provided news.

Design:
- Structured output validated by Pydantic (`messages.parse`): the API is
  constrained to the schema, and the SDK validates it again on our side.
- Sources are passed as a numbered list and the model returns the NUMBERS,
  not URLs. We map numbers back to URLs ourselves, so the model cannot
  invent or mistype a link; an out-of-range number is caught by validation.
- If the headlines do not explain the move, the model must say so
  ("no clear explanation") instead of guessing.
"""
import time
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from src.config import COMPANY_NAMES, MODEL, OUTPUT_LANGUAGE, PRICE_PER_MTOK

NO_EXPLANATION = "no clear explanation"

SYSTEM_PROMPT = f"""You are a financial analyst explaining unusual daily moves of Brazilian stocks (B3) to retail investors.

You receive one event (stock, date, return, Ibovespa return that day) and a numbered list of news headlines published around that date.

Rules:
- Use ONLY the numbered headlines. Do not use outside knowledge about what happened; you may use general finance knowledge to interpret the headlines.
- Cite the headlines that support your explanation by their numbers in `source_ids`. Cite only headlines that actually support it.
- If the headlines do not explain the move (irrelevant, only describe the price change without a cause, or contradict the direction), set short_reason to exactly "{NO_EXPLANATION}", type to "unknown", confidence to "low", and source_ids to [].
- type: "company" (company-specific: earnings, guidance, management, deals), "sector" (affects the sector: oil price, iron ore, retail, banks), "macro" (whole market: elections, interest rates, fiscal, global risk).
- confidence: "high" if several headlines state the cause directly; "medium" if one headline states it or it is a reasonable inference; "low" if weak.
- short_reason: max 8 words. explanation: 2-3 sentences, factual, no investment advice.
- Write short_reason and explanation in {OUTPUT_LANGUAGE}."""


class Explanation(BaseModel):
    short_reason: str = Field(description="Max 8 words, e.g. 'Lucro do 3T abaixo do esperado'")
    explanation: str = Field(description="2-3 sentences explaining the move")
    type: Literal["company", "sector", "macro", "unknown"]
    confidence: Literal["high", "medium", "low"]
    source_ids: list[int] = Field(description="Numbers of the headlines that support the explanation")


def build_user_message(ticker: str, event: dict, news: list[dict]) -> str:
    headlines = "\n".join(
        f"[{i}] ({n['published']}, {n['source']}) {n['title']}" for i, n in enumerate(news, 1)
    ) or "(no headlines found)"
    return (
        f"Stock: {ticker} ({COMPANY_NAMES[ticker]})\n"
        f"Date: {event['date']}\n"
        f"Stock return: {event['return']:+.2%} (z-score {event['z']:+.1f})\n"
        f"Ibovespa return: {event['ibov_return']:+.2%}\n"
        f"Detector scope: {event['scope']} "
        f"({'market-wide move' if event['scope'] == 'market' else 'stock-specific move'})\n\n"
        f"Headlines:\n{headlines}"
    )


def explain_event(client: anthropic.Anthropic, ticker: str, event: dict, news: list[dict]) -> dict:
    started = time.perf_counter()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=2000,
        output_config={"effort": "medium"},  # Haiku 5.5 default, made explicit
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(ticker, event, news)}],
        output_format=Explanation,
    )
    latency = time.perf_counter() - started

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused for {ticker} {event['date']}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"Output truncated for {ticker} {event['date']}")

    out: Explanation = response.parsed_output
    # Grounding guard: keep only ids that exist in the list we sent.
    valid_ids = [i for i in out.source_ids if 1 <= i <= len(news)]
    usage = response.usage
    cost = (usage.input_tokens * PRICE_PER_MTOK["input"]
            + usage.output_tokens * PRICE_PER_MTOK["output"]) / 1_000_000

    return {
        "short_reason": out.short_reason,
        "explanation": out.explanation,
        "type": out.type,
        "confidence": out.confidence,
        "sources": [{"title": news[i - 1]["title"], "source": news[i - 1]["source"],
                     "url": news[i - 1]["url"]} for i in valid_ids],
        "meta": {
            "model": MODEL,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": round(cost, 6),
            "latency_s": round(latency, 2),
            "invalid_source_ids": [i for i in out.source_ids if i not in valid_ids],
        },
    }


def main() -> None:
    """Smoke test on 3 known events (3 API calls, well under $0.01)."""
    import json
    import os
    import sys

    from src.detect import detect_events
    from src.news import fetch_news

    sys.stdout.reconfigure(encoding="utf-8")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is empty: fill it in .env (and save the file).")
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY loaded from .env by config
    samples = [("MGLU3", "2026-10-26"), ("PETR4", "2026-11-04"), ("WEGE3", "2026-10-21")]
    total = 0.0
    for ticker, day in samples:
        event = next(e for e in detect_events(ticker) if e["date"] == day)
        result = explain_event(client, ticker, event, fetch_news(ticker, event))
        total += result["meta"]["cost_usd"]
        print(f"\n=== {ticker} {day} ({event['return']:+.2%}) ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nTotal cost: ${total:.5f}")


if __name__ == "__main__":
    main()
