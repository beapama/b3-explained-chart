"""Step 5: ask Claude to explain a strong move using only the headlines provided.

Design:

* Structured output validated by Pydantic (``messages.parse``): the API is
  constrained to the ``Explanation`` schema and the SDK validates it again.
* Headlines are sent as a numbered list and the model returns the numbers,
  not URLs. The code maps numbers back to links, so the model cannot invent
  or mistype a source; an out-of-range number is dropped and logged.
* If the headlines do not explain the move, the model answers
  ``NO_EXPLANATION`` instead of guessing.
* The English fields are written in the same call, at no extra request, for
  the site's English version. ``Explanation`` has no class docstring on
  purpose: Pydantic would send it to the API as the schema description.

Usage:
    python -m src.explain    Smoke test on three known events (three API calls).
"""

import json
import sys
import time
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from src.config import COMPANY_NAMES, MODEL, OUTPUT_LANGUAGE, require_api_key, token_cost_usd

NO_EXPLANATION = "no clear explanation"
MAX_TOKENS = 2000
EFFORT = "medium"
COST_DECIMALS = 6
LATENCY_DECIMALS = 2

SYSTEM_PROMPT = f"""You are a financial analyst explaining unusual daily moves of Brazilian stocks (B3) to retail investors.

You receive one event (stock, date, return, Ibovespa return that day) and a numbered list of news headlines published around that date.

Rules:
- Use ONLY the numbered headlines. Do not use outside knowledge about what happened; you may use general finance knowledge to interpret the headlines.
- Cite the headlines that support your explanation by their numbers in `source_ids`. Cite only headlines that actually support it.
- If the headlines do not explain the move (irrelevant, only describe the price change without a cause, or contradict the direction), set short_reason to exactly "{NO_EXPLANATION}", type to "unknown", confidence to "low", and source_ids to [].
- type: "company" (company-specific: earnings, guidance, management, deals), "sector" (affects the sector: oil price, iron ore, retail, banks), "macro" (whole market: elections, interest rates, fiscal, global risk).
- confidence: "high" if several headlines state the cause directly; "medium" if one headline states it or it is a reasonable inference; "low" if weak.
- short_reason: max 8 words. explanation: 2-3 sentences, factual, no investment advice.
- Write short_reason and explanation in {OUTPUT_LANGUAGE}.
- Also write short_reason_en and explanation_en: the same content in clear English, for international readers (same facts, no additions). If there is no clear explanation, short_reason_en is exactly "{NO_EXPLANATION}"."""


class Explanation(BaseModel):
    short_reason: str = Field(description="Max 8 words, e.g. 'Lucro do 3T abaixo do esperado'")
    explanation: str = Field(description="2-3 sentences explaining the move")
    type: Literal["company", "sector", "macro", "unknown"]
    confidence: Literal["high", "medium", "low"]
    source_ids: list[int] = Field(description="Numbers of the headlines that support the explanation")
    short_reason_en: str = Field(description="short_reason in English, max 8 words")
    explanation_en: str = Field(description="explanation in English")


def build_user_message(ticker: str, event: dict, news: list[dict]) -> str:
    """Return the user message: the event's numbers followed by the numbered headlines."""
    headlines = (
        "\n".join(f"[{i}] ({n['published']}, {n['source']}) {n['title']}" for i, n in enumerate(news, 1))
        or "(no headlines found)"
    )
    scope_text = "market-wide move" if event["scope"] == "market" else "stock-specific move"
    return (
        f"Stock: {ticker} ({COMPANY_NAMES[ticker]})\n"
        f"Date: {event['date']}\n"
        f"Stock return: {event['return']:+.2%} (z-score {event['z']:+.1f})\n"
        f"Ibovespa return: {event['ibov_return']:+.2%}\n"
        f"Detector scope: {event['scope']} ({scope_text})\n\n"
        f"Headlines:\n{headlines}"
    )


def check_stop_reason(response, label: str) -> None:
    """Raise when the model refused or the answer was cut by the token limit."""
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused for {label}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"Output truncated for {label}")


def explain_event(client: anthropic.Anthropic, ticker: str, event: dict, news: list[dict]) -> dict:
    """Explain one event and return the record stored under ``"ai"`` in the cache.

    Only source numbers that exist in ``news`` become links; the others are
    kept in ``meta.invalid_source_ids`` for the evaluation.
    """
    started = time.perf_counter()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(ticker, event, news)}],
        output_format=Explanation,
    )
    latency = time.perf_counter() - started
    check_stop_reason(response, f"{ticker} {event['date']}")

    out: Explanation = response.parsed_output
    valid_ids = [i for i in out.source_ids if 1 <= i <= len(news)]
    usage = response.usage
    return {
        "short_reason": out.short_reason,
        "explanation": out.explanation,
        "short_reason_en": out.short_reason_en,
        "explanation_en": out.explanation_en,
        "type": out.type,
        "confidence": out.confidence,
        "sources": [
            {"title": news[i - 1]["title"], "source": news[i - 1]["source"], "url": news[i - 1]["url"]}
            for i in valid_ids
        ],
        "meta": {
            "model": MODEL,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": round(token_cost_usd(usage.input_tokens, usage.output_tokens), COST_DECIMALS),
            "latency_s": round(latency, LATENCY_DECIMALS),
            "invalid_source_ids": [i for i in out.source_ids if i not in valid_ids],
        },
    }


def main() -> None:
    """Explain three known events and print the results with their total cost."""
    from src.detect import detect_events
    from src.news import fetch_news

    sys.stdout.reconfigure(encoding="utf-8")
    require_api_key(".env (and save the file)")
    client = anthropic.Anthropic()
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
