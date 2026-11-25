"""Step 8: assemble the static site into ``_site/``, the folder GitHub Pages serves.

Copies ``site/`` and only the data the browser needs (prices, events, the
evaluation summary) plus an ``index.json`` with the ticker list. The same
command runs locally and in CI, so what is tested is what ships.

Usage:
    python -m src.build_site                 Build the site.
    python -m http.server 8000 -d _site      Serve it at http://localhost:8000.
"""

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from src.config import COMPANY_NAMES, EVAL_DIR, EVENTS_DIR, INDEX_NAME, PRICES_DIR, ROOT, TICKERS

SITE_SRC = ROOT / "site"
OUT = ROOT / "_site"
OUT_DATA = OUT / "data"
VERSIONED_ASSETS = ("style.css", "app.js")
HASH_LENGTH = 8


def bust_cache(html_path: Path) -> None:
    """Add a content hash to the CSS and JS links: ``style.css`` -> ``style.css?v=1a2b3c4d``.

    GitHub Pages lets browsers cache files for ten minutes. Without the hash a
    visitor right after a deploy could get the new HTML with the old JavaScript
    and the page would stop at "Carregando...". A new hash means a new URL.
    """
    html = html_path.read_text(encoding="utf-8")
    for name in VERSIONED_ASSETS:
        digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()[:HASH_LENGTH]
        html = html.replace(f'"{name}"', f'"{name}?v={digest}"')
    html_path.write_text(html, encoding="utf-8")


def write_index() -> None:
    """Write ``data/index.json``: build time, index name and the ticker list."""
    index = {
        "updated_at": datetime.now(UTC).isoformat(timespec="minutes"),
        "index": INDEX_NAME,
        "tickers": [{"ticker": t, "name": COMPANY_NAMES[t]} for t in TICKERS],
    }
    (OUT_DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    """Rebuild ``_site/`` from scratch."""
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SITE_SRC, OUT)
    bust_cache(OUT / "index.html")
    skip_placeholders = shutil.ignore_patterns(".gitkeep")
    shutil.copytree(PRICES_DIR, OUT_DATA / "prices", ignore=skip_placeholders)
    shutil.copytree(EVENTS_DIR, OUT_DATA / "events", ignore=skip_placeholders)
    shutil.copy(EVAL_DIR / "summary.json", OUT_DATA / "eval_summary.json")
    write_index()
    print(f"Site built in {OUT}")


if __name__ == "__main__":
    main()
