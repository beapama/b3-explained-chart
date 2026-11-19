"""Central configuration: universe, paths and parameters shared by all steps."""
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # no-op in GitHub Actions, where secrets come from env vars

# Universe (B3 tickers need the .SA suffix on Yahoo Finance)
TICKERS = ["PETR4", "VALE3", "ITUB4", "MGLU3", "WEGE3"]
INDEX = "^BVSP"  # Ibovespa on Yahoo
INDEX_NAME = "IBOV"  # file name / label used everywhere else
LOOKBACK_DAYS = 365

# Paths
DATA_DIR = ROOT / "data"
PRICES_DIR = DATA_DIR / "prices"
EVENTS_DIR = DATA_DIR / "events"
EVAL_DIR = DATA_DIR / "eval"


def yahoo_symbol(ticker: str) -> str:
    """PETR4 -> PETR4.SA; index symbols (starting with ^) pass through."""
    return ticker if ticker.startswith("^") else f"{ticker}.SA"
