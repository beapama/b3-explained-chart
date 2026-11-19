"""Step 3: detect strong daily moves with a rolling z-score.

z = (return_today - mean) / std, where mean and std come from the previous
Z_WINDOW days only (shift(1)): today's move must not inflate its own baseline.
Each event is also compared with the Ibovespa on the same day to tell a
stock-specific move from a market-wide one.
"""
import json
from datetime import date, timedelta

import pandas as pd

from src.config import (
    INDEX_NAME, LOOKBACK_DAYS, MARKET_Z_THRESHOLD, PRICES_DIR, TICKERS,
    Z_THRESHOLD, Z_WINDOW,
)


def load_returns(name: str) -> pd.Series:
    rows = json.loads((PRICES_DIR / f"{name}.json").read_text())
    close = pd.DataFrame(rows).set_index("time")["close"]
    return close.pct_change()


def zscore(returns: pd.Series) -> pd.Series:
    baseline = returns.rolling(Z_WINDOW, min_periods=Z_WINDOW)
    return (returns - baseline.mean().shift(1)) / baseline.std().shift(1)


def detect_events(ticker: str) -> list[dict]:
    ret, ibov_ret = load_returns(ticker), load_returns(INDEX_NAME)
    df = pd.DataFrame({
        "ret": ret, "z": zscore(ret),
        "ibov_ret": ibov_ret, "ibov_z": zscore(ibov_ret),
    }).dropna()

    cutoff = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    strong = df[(df.z.abs() >= Z_THRESHOLD) & (df.index >= cutoff)]

    events = []
    for day, r in strong.iterrows():
        same_direction = (r.ret > 0) == (r.ibov_ret > 0)
        market_wide = abs(r.ibov_z) >= MARKET_Z_THRESHOLD and same_direction
        events.append({
            "date": day,
            "return": round(r.ret, 4),
            "z": round(r.z, 2),
            "ibov_return": round(r.ibov_ret, 4),
            "excess_return": round(r.ret - r.ibov_ret, 4),  # simple market adjustment
            "scope": "market" if market_wide else "stock",
        })
    return events


def main() -> None:
    total = 0
    for t in TICKERS:
        events = detect_events(t)
        total += len(events)
        print(f"\n{t}: {len(events)} events")
        for e in events:
            print(f"  {e['date']}  ret {e['return']:+7.2%}  z {e['z']:+5.1f}  "
                  f"ibov {e['ibov_return']:+6.2%}  [{e['scope']}]")
    print(f"\nTotal: {total} events")


if __name__ == "__main__":
    main()
