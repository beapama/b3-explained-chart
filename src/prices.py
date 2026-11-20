"""Step 2: download daily adjusted prices from Yahoo Finance and save as JSON.

Output: data/prices/{TICKER}.json -> [{"time": "YYYY-MM-DD", "open", "high",
"low", "close", "volume"}, ...]. The shape matches what lightweight-charts
expects, so the site can plot the file without any transformation.
"""
import json
from datetime import date, timedelta

import yfinance as yf

from src.config import INDEX, INDEX_NAME, LOOKBACK_DAYS, PRICES_DIR, TICKERS, WARMUP_DAYS, yahoo_symbol


def fetch_prices(symbol: str, start: date) -> list[dict]:
    # auto_adjust=True: prices adjusted for dividends and splits, so a
    # dividend ex-date does not look like a fake "crash" in daily returns.
    df = yf.Ticker(symbol).history(start=start.isoformat(), auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")
    # Yahoo sometimes returns the current/last day with volume but NaN prices
    # (seen when running around midnight). Drop it; the next run picks it up.
    bad = df[["Open", "High", "Low", "Close"]].isna().any(axis=1)
    if bad.any():
        print(f"  warning: {symbol} dropped {bad.sum()} row(s) with missing prices: "
              f"{[d.strftime('%Y-%m-%d') for d in df.index[bad]]}")
        df = df[~bad]
    return [
        {
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(float(row.Open), 4),
            "high": round(float(row.High), 4),
            "low": round(float(row.Low), 4),
            "close": round(float(row.Close), 4),
            "volume": int(row.Volume),
        }
        for ts, row in df.iterrows()
    ]


def save(name: str, rows: list[dict]) -> None:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    # allow_nan=False: NaN is not valid JSON and would break the site; fail loudly instead.
    (PRICES_DIR / f"{name}.json").write_text(json.dumps(rows, indent=1, allow_nan=False))


def main() -> None:
    # Extra warm-up history so the detector's rolling window is full on day 1.
    start = date.today() - timedelta(days=LOOKBACK_DAYS + WARMUP_DAYS)
    # Full re-download every run: 6 free requests, and it picks up any
    # retroactive adjustment (new dividend) without incremental-merge logic.
    for name, symbol in [(t, yahoo_symbol(t)) for t in TICKERS] + [(INDEX_NAME, INDEX)]:
        rows = fetch_prices(symbol, start)
        save(name, rows)
        print(f"{name:6} {len(rows):4} days  {rows[0]['time']} -> {rows[-1]['time']}  last close {rows[-1]['close']}")


if __name__ == "__main__":
    main()
