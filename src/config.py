"""Central configuration: universe, paths and parameters shared by all steps."""

from pathlib import Path



from dotenv import load_dotenv



ROOT = Path(__file__).resolve().parent.parent

# override=True: the local .env wins over stale/empty shell variables (VS Code
# injects .env into terminals when they open). No-op in GitHub Actions, where
# there is no .env and secrets come from env vars.
load_dotenv(ROOT / ".env", override=True)



# Universe (B3 tickers need the .SA suffix on Yahoo Finance)

TICKERS = ["PETR4", "VALE3", "ITUB4", "MGLU3", "WEGE3"]

# Names used in news search (ticker alone misses most headlines)

COMPANY_NAMES = {

    "PETR4": "Petrobras",

    "VALE3": "Vale",

    "ITUB4": "Itaú",

    "MGLU3": "Magazine Luiza",

    "WEGE3": "WEG",

}

INDEX = "^BVSP"  # Ibovespa on Yahoo

INDEX_NAME = "IBOV"  # file name / label used everywhere else

LOOKBACK_DAYS = 365  # period shown on the site and scanned for events

WARMUP_DAYS = 100  # extra calendar days so the rolling z-score is ready on day 1



# Strong-move detection

Z_WINDOW = 60  # trading days (~3 months) used for mean/std of daily returns

Z_THRESHOLD = 2.5  # |z| >= this is a strong move for the stock

MARKET_Z_THRESHOLD = 2.0  # |z| of Ibovespa >= this, same direction -> market-wide move



# Paths

DATA_DIR = ROOT / "data"

PRICES_DIR = DATA_DIR / "prices"

EVENTS_DIR = DATA_DIR / "events"

EVAL_DIR = DATA_DIR / "eval"





def yahoo_symbol(ticker: str) -> str:

    """PETR4 -> PETR4.SA; index symbols (starting with ^) pass through."""

    return ticker if ticker.startswith("^") else f"{ticker}.SA"



# News

NEWS_PER_EVENT = 10  # max articles sent to the model per event (~2k input tokens)
MARKET_NEWS_SLOTS = 5  # of those, reserved for market news on market-wide moves


# AI explanation
MODEL = "claude-haiku-5-5"  # small and cheap: short structured answer over ~8 headlines
PRICE_PER_MTOK = {"input": 0.10, "output": 0.50}  # USD, used to log cost per run
OUTPUT_LANGUAGE = "Brazilian Portuguese"  # sources are Brazilian; site audience too
