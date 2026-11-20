"""Step 8: assemble the static site into _site/ (what GitHub Pages serves).

Copies site/ (HTML/CSS/JS) and only the data the browser needs:
prices, events and the eval summary, plus a small index.json with the
ticker list. Same command locally and in CI, so what you test is what ships.

Usage:
    python -m src.build_site
    python -m http.server 8000 -d _site     # open http://localhost:8000
"""
import hashlib
import json
import shutil
from datetime import datetime, timezone

from src.config import COMPANY_NAMES, EVAL_DIR, EVENTS_DIR, INDEX_NAME, PRICES_DIR, ROOT, TICKERS

SITE_SRC = ROOT / "site"
OUT = ROOT / "_site"


def bust_cache(html_path) -> None:
    """Add a content hash to the CSS/JS links: style.css -> style.css?v=1a2b3c4d.

    GitHub Pages lets browsers cache files for 10 minutes. Without this, a
    visitor right after a deploy could get the new HTML with the old JS (seen:
    the page stuck on "Carregando..."). A new hash = a new URL = a fresh download.
    """
    html = html_path.read_text(encoding="utf-8")
    for name in ("style.css", "app.js"):
        digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()[:8]
        html = html.replace(f'"{name}"', f'"{name}?v={digest}"')
    html_path.write_text(html, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SITE_SRC, OUT)
    bust_cache(OUT / "index.html")
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
