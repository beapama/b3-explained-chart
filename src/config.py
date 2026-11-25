"""Configuration shared by every step: universe, paths, detection, news and AI settings.

The local ``.env`` is loaded with ``override=True`` so it wins over stale or
empty variables that an editor may have injected into the terminal. In GitHub
Actions there is no ``.env`` and the API key comes from the repository secret.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

TICKERS = ["PETR4", "VALE3", "ITUB4", "MGLU3", "WEGE3"]
"""B3 tickers covered by the site."""

COMPANY_NAMES = {
    "PETR4": "Petrobras",
    "VALE3": "Vale",
    "ITUB4": "Itaú",
    "MGLU3": "Magazine Luiza",
    "WEGE3": "WEG",
}
"""Names used in news search; the ticker alone misses most headlines."""

INDEX = "^BVSP"
"""Ibovespa symbol on Yahoo Finance."""

INDEX_NAME = "IBOV"
"""File name and label used for the Ibovespa everywhere else."""

LOOKBACK_DAYS = 365
"""Calendar days shown on the site and scanned for events."""

WARMUP_DAYS = 100
"""Extra calendar days downloaded so the rolling window is full on the first shown day."""

Z_WINDOW = 60
"""Trading days (about three months) used for the mean and std of daily returns."""

Z_THRESHOLD = 2.5
"""A day is a strong move when the stock's |z| reaches this value."""

MARKET_Z_THRESHOLD = 2.0
"""A strong move is market-wide when the Ibovespa's |z| reaches this value in the same direction."""

DATA_DIR = ROOT / "data"
PRICES_DIR = DATA_DIR / "prices"
EVENTS_DIR = DATA_DIR / "events"
EVAL_DIR = DATA_DIR / "eval"

NEWS_PER_EVENT = 10
"""Maximum headlines sent to the model per event (about 2k input tokens)."""

MARKET_NEWS_SLOTS = 5
"""Headlines reserved for market news on market-wide moves."""

MODEL = "claude-haiku-5-5"
"""Small, cheap model: a short structured answer over a few headlines."""

PRICE_PER_MTOK = {"input": 0.10, "output": 0.50}
"""USD per million tokens, used to log the cost of each run."""

OUTPUT_LANGUAGE = "Brazilian Portuguese"
"""Primary language of the explanations; the sources are Brazilian."""


def yahoo_symbol(ticker: str) -> str:
    """Return the Yahoo Finance symbol: ``PETR4`` -> ``PETR4.SA``; index symbols pass through."""
    return ticker if ticker.startswith("^") else f"{ticker}.SA"


def token_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Return the USD cost of one API call from its token usage."""
    return (input_tokens * PRICE_PER_MTOK["input"] + output_tokens * PRICE_PER_MTOK["output"]) / 1_000_000


def require_api_key(where: str) -> None:
    """Exit with a clear message when ``ANTHROPIC_API_KEY`` is missing or empty."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(f"ANTHROPIC_API_KEY is empty: fill it in {where}.")
