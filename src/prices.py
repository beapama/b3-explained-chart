"""Step 2: download daily adjusted prices from Yahoo Finance and save them as JSON.

Each file ``data/prices/{TICKER}.json`` is a list of
``{"time", "open", "high", "low", "close", "volume"}`` rows, the shape
lightweight-charts expects, so the site plots it without transformation.

Prices are adjusted for dividends and splits, otherwise an ex-dividend date
would look like a crash. The whole history is downloaded on every run: six
free requests, and any retroactive adjustment is picked up without merge logic.

Usage:
    python -m src.prices
"""

import json
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from src.config import INDEX, INDEX_NAME, LOOKBACK_DAYS, PRICES_DIR, TICKERS, WARMUP_DAYS, yahoo_symbol

PRICE_COLUMNS = ["Open", "High", "Low", "Close"]
PRICE_DECIMALS = 4
DATE_FORMAT = "%Y-%m-%d"


def drop_missing_prices(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Drop rows without prices.

    Around midnight Yahoo returns the latest day with volume but NaN prices;
    the next run picks that day up complete.
    """
    missing = df[PRICE_COLUMNS].isna().any(axis=1)
    if missing.any():
        days = [d.strftime(DATE_FORMAT) for d in df.index[missing]]
        print(f"  warning: {symbol} dropped {missing.sum()} row(s) with missing prices: {days}")
    return df[~missing]


def fetch_prices(symbol: str, start: date) -> list[dict]:
    """Return adjusted daily bars for ``symbol`` from ``start`` to today."""
    df = yf.Ticker(symbol).history(start=start.isoformat(), auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")
    df = drop_missing_prices(df, symbol)
    return [
        {
            "time": ts.strftime(DATE_FORMAT),
            "open": round(float(row.Open), PRICE_DECIMALS),
            "high": round(float(row.High), PRICE_DECIMALS),
            "low": round(float(row.Low), PRICE_DECIMALS),
            "close": round(float(row.Close), PRICE_DECIMALS),
            "volume": int(row.Volume),
        }
        for ts, row in df.iterrows()
    ]


def save(name: str, rows: list[dict]) -> None:
    """Write the bars to ``data/prices/{name}.json``, refusing NaN (invalid JSON for the site)."""
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    (PRICES_DIR / f"{name}.json").write_text(json.dumps(rows, indent=1, allow_nan=False))


def download_all() -> None:
    """Download every ticker and the Ibovespa, with warm-up history for the detector."""
    start = date.today() - timedelta(days=LOOKBACK_DAYS + WARMUP_DAYS)
    symbols = [(t, yahoo_symbol(t)) for t in TICKERS] + [(INDEX_NAME, INDEX)]
    for name, symbol in symbols:
        rows = fetch_prices(symbol, start)
        save(name, rows)
        print(f"{name:6} {len(rows):4} days  {rows[0]['time']} -> {rows[-1]['time']}  last close {rows[-1]['close']}")


if __name__ == "__main__":
    download_all()
