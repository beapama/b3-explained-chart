"""Step 2: download daily adjusted prices from Yahoo Finance and save as JSON.

Output: data/prices/{TICKER}.json -> [{"time": "YYYY-MM-DD", "open", "high",
"low", "close", "volume"}, ...]. The shape matches what lightweight-charts
expects, so the site can plot the file without any transformation.
"""
import json
from datetime import date, timedelta

import yfinance as yf

from src.config import INDEX, INDEX_NAME, LOOKBACK_DAYS, PRICES_DIR, TICKERS, yahoo_symbol


def fetch_prices(symbol: str, start: date) -> list[dict]:
    # auto_adjust=True: prices adjusted for dividends and splits, so a
    # dividend ex-date does not look like a fake "crash" in daily returns.
    df = yf.Ticker(symbol).history(start=start.isoformat(), auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")
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
    (PRICES_DIR / f"{name}.json").write_text(json.dumps(rows, indent=1))


def main() -> None:
    start = date.today() - timedelta(days=LOOKBACK_DAYS)
    # Full re-download every run: 6 free requests, and it picks up any
    # retroactive adjustment (new dividend) without incremental-merge logic.
    for name, symbol in [(t, yahoo_symbol(t)) for t in TICKERS] + [(INDEX_NAME, INDEX)]:
        rows = fetch_prices(symbol, start)
        save(name, rows)
        print(f"{name:6} {len(rows):4} days  {rows[0]['time']} -> {rows[-1]['time']}  last close {rows[-1]['close']}")


if __name__ == "__main__":
    main()
