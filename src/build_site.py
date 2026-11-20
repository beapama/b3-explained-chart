"""Step 8: assemble the static site into _site/ (what GitHub Pages serves).

Copies site/ (HTML/CSS/JS) and only the data the browser needs:
prices, events and the eval summary, plus a small index.json with the
ticker list. Same command locally and in CI, so what you test is what ships.

Usage:
    python -m src.build_site
    python -m http.server 8000 -d _site     # open http://localhost:8000
"""
import json
import shutil
from datetime import datetime, timezone

from src.config import COMPANY_NAMES, EVAL_DIR, EVENTS_DIR, INDEX_NAME, PRICES_DIR, ROOT, TICKERS

SITE_SRC = ROOT / "site"
OUT = ROOT / "_site"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SITE_SRC, OUT)
    shutil.copytree(PRICES_DIR, OUT / "data" / "prices", ignore=shutil.ignore_patterns(".gitkeep"))
    shutil.copytree(EVENTS_DIR, OUT / "data" / "events", ignore=shutil.ignore_patterns(".gitkeep"))
    shutil.copy(EVAL_DIR / "summary.json", OUT / "data" / "eval_summary.json")

    index = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "index": INDEX_NAME,
        "tickers": [{"ticker": t, "name": COMPANY_NAMES[t]} for t in TICKERS],
    }
    (OUT / "data" / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"Site built in {OUT}")


if __name__ == "__main__":
    main()
