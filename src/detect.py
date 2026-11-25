"""Step 3: detect strong daily moves with a rolling z-score.

``z = (return_today - mean) / std``, where the mean and std come from the
previous ``Z_WINDOW`` trading days only, so a move cannot inflate its own
baseline. Each event is compared with the Ibovespa on the same day to tell a
stock-specific move from a market-wide one.

Usage:
    python -m src.detect
"""

import json
from datetime import date, timedelta

import pandas as pd

from src.config import INDEX_NAME, LOOKBACK_DAYS, MARKET_Z_THRESHOLD, PRICES_DIR, TICKERS, Z_THRESHOLD, Z_WINDOW

RETURN_DECIMALS = 4
Z_DECIMALS = 2


def load_returns(name: str) -> pd.Series:
    """Return daily close-to-close returns indexed by ISO date."""
    rows = json.loads((PRICES_DIR / f"{name}.json").read_text())
    close = pd.DataFrame(rows).set_index("time")["close"]
    return close.pct_change()


def zscore(returns: pd.Series) -> pd.Series:
    """Return each day's z-score against the previous ``Z_WINDOW`` days, excluding the day itself."""
    baseline = returns.rolling(Z_WINDOW, min_periods=Z_WINDOW)
    return (returns - baseline.mean().shift(1)) / baseline.std().shift(1)


def daily_table(ticker: str) -> pd.DataFrame:
    """Return returns and z-scores of the stock and the Ibovespa, plus the previous trading day.

    The previous trading day starts the news window, so weekend news (an
    election on Sunday, for example) is included for a Monday move.
    """
    ret, ibov_ret = load_returns(ticker), load_returns(INDEX_NAME)
    df = pd.DataFrame({"ret": ret, "z": zscore(ret), "ibov_ret": ibov_ret, "ibov_z": zscore(ibov_ret)})
    df["prev_date"] = pd.Series(df.index, index=df.index).shift(1)
    return df.dropna()


def is_market_wide(row: pd.Series) -> bool:
    """Return True when the Ibovespa also moved strongly, in the same direction."""
    same_direction = (row.ret > 0) == (row.ibov_ret > 0)
    return abs(row.ibov_z) >= MARKET_Z_THRESHOLD and same_direction


def to_event(day: str, row: pd.Series) -> dict:
    """Build the event record stored in the cache and shown on the site."""
    return {
        "date": day,
        "prev_date": row.prev_date,
        "return": round(row.ret, RETURN_DECIMALS),
        "z": round(row.z, Z_DECIMALS),
        "ibov_return": round(row.ibov_ret, RETURN_DECIMALS),
        "excess_return": round(row.ret - row.ibov_ret, RETURN_DECIMALS),
        "scope": "market" if is_market_wide(row) else "stock",
    }


def detect_events(ticker: str) -> list[dict]:
    """Return the strong-move events of ``ticker`` within the last ``LOOKBACK_DAYS``."""
    df = daily_table(ticker)
    cutoff = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    strong = df[(df.z.abs() >= Z_THRESHOLD) & (df.index >= cutoff)]
    return [to_event(day, row) for day, row in strong.iterrows()]


def main() -> None:
    """Print every detected event per ticker."""
    total = 0
    for ticker in TICKERS:
        events = detect_events(ticker)
        total += len(events)
        print(f"\n{ticker}: {len(events)} events")
        for e in events:
            print(
                f"  {e['date']}  ret {e['return']:+7.2%}  z {e['z']:+5.1f}  "
                f"ibov {e['ibov_return']:+6.2%}  [{e['scope']}]"
            )
    print(f"\nTotal: {total} events")


if __name__ == "__main__":
    main()
