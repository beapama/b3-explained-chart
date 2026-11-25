"""Step 7: evaluation on the stored events, with no API calls.

Two layers:

1. Automatic checks on every event: each cited source is one of the headlines
   the model received; abstentions cite nothing and have type ``unknown``;
   real answers cite at least one source; how often the AI calls market-wide
   days "macro".
2. Labels on a fixed sample of 15 events, stratified by type so abstentions
   are judged too: accuracy (a partial answer counts as half), accuracy by
   confidence level and type accuracy.

The labels CSV uses ``utf-8-sig`` and ``;`` so Excel in Portuguese opens it
with accents and columns right. ``LABELER`` is shown on the site, so it must
stay honest: set ``human_reviewed`` to True only after a person checked
``labels.csv``.

Usage:
    python -m src.evaluate sample    Draw the sample into data/eval/labels.csv.
    python -m src.evaluate           Write data/eval/summary.json, read by the site.
"""

import csv
import json
import random
import sys
from collections import Counter
from datetime import UTC, datetime

from src.config import EVAL_DIR, EVENTS_DIR, MODEL, TICKERS
from src.explain import NO_EXPLANATION

LABELS_PATH = EVAL_DIR / "labels.csv"
SUMMARY_PATH = EVAL_DIR / "summary.json"
RUNS_LOG = EVAL_DIR / "runs.jsonl"
SAMPLE_PER_TYPE = {"macro": 4, "company": 4, "sector": 3, "unknown": 4}
SEED = 42
LABELER = {"model": "Claude Opus 5.5", "method": "llm-as-judge", "human_reviewed": False}
LABEL_SCORES = {"yes": 1.0, "partial": 0.5, "no": 0.0}
CONFIDENCE_LEVELS = ("high", "medium", "low")
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8-sig"
CSV_HEADER = [
    "ticker",
    "date",
    "return",
    "ibov_return",
    "ai_type",
    "ai_confidence",
    "ai_short_reason",
    "ai_explanation",
    "headlines_given",
    "label_correct",
    "label_type",
    "notes",
]


def percent(part: float, whole: float) -> float | None:
    """Return ``part / whole`` as a percentage with one decimal, or None when ``whole`` is zero."""
    return round(100 * part / whole, 1) if whole else None


def load_events() -> list[dict]:
    """Return every cached event, tagged with its ticker."""
    events = []
    for ticker in TICKERS:
        path = EVENTS_DIR / f"{ticker}.json"
        if path.exists():
            events += [{"ticker": ticker, **e} for e in json.loads(path.read_text(encoding="utf-8"))]
    return events


def is_abstention(event: dict) -> bool:
    """Return True when the model said the headlines do not explain the move."""
    return event["ai"]["short_reason"] == NO_EXPLANATION


def is_consistent(event: dict) -> bool:
    """Return True when an abstention cites nothing and a real answer cites at least one source."""
    ai = event["ai"]
    if is_abstention(event):
        return ai["type"] == "unknown" and not ai["sources"]
    return bool(ai["sources"])


def automatic_checks(events: list[dict]) -> dict:
    """Return the checks that run on every event."""
    cited = grounded = 0
    for e in events:
        provided = {n["url"] for n in e["news"]}
        for source in e["ai"]["sources"]:
            cited += 1
            grounded += source["url"] in provided

    market = [e for e in events if e["scope"] == "market"]
    explained = [e for e in events if not is_abstention(e)]
    return {
        "events": len(events),
        "explained": len(explained),
        "no_clear_explanation": len(events) - len(explained),
        "sources_cited": cited,
        "sources_grounded_pct": percent(grounded, cited),
        "invalid_source_ids": sum(len(e["ai"]["meta"]["invalid_source_ids"]) for e in events),
        "inconsistent_answers": [f"{e['ticker']} {e['date']}" for e in events if not is_consistent(e)],
        "market_scope_labeled_macro_pct": percent(sum(e["ai"]["type"] == "macro" for e in market), len(market)),
        "by_type": dict(Counter(e["ai"]["type"] for e in events)),
        "by_confidence": dict(Counter(e["ai"]["confidence"] for e in events)),
    }


def draw_sample(events: list[dict]) -> list[dict]:
    """Return a reproducible sample stratified by type, sorted by ticker and date."""
    rng = random.Random(SEED)
    sample = []
    for event_type, size in SAMPLE_PER_TYPE.items():
        pool = [e for e in events if e["ai"]["type"] == event_type]
        sample += rng.sample(pool, min(size, len(pool)))
    return sorted(sample, key=lambda e: (e["ticker"], e["date"]))


def label_row(event: dict) -> list[str]:
    """Return one CSV row with the AI's answer, the headlines it read and empty label columns."""
    ai = event["ai"]
    headlines = " | ".join(f"[{i}] {n['title']}" for i, n in enumerate(event["news"], 1))
    return [
        event["ticker"],
        event["date"],
        f"{event['return']:+.2%}",
        f"{event['ibov_return']:+.2%}",
        ai["type"],
        ai["confidence"],
        ai["short_reason"],
        ai["explanation"],
        headlines,
        "",
        "",
        "",
    ]


def create_sample(events: list[dict]) -> None:
    """Write the labeling sheet, refusing to overwrite labels already made."""
    if LABELS_PATH.exists():
        sys.exit(f"{LABELS_PATH} already exists; delete it to draw a new sample.")
    sample = draw_sample(events)
    with open(LABELS_PATH, "w", newline="", encoding=CSV_ENCODING) as f:
        writer = csv.writer(f, delimiter=CSV_DELIMITER)
        writer.writerow(CSV_HEADER)
        writer.writerows(label_row(e) for e in sample)
    print(f"Wrote {len(sample)} events to {LABELS_PATH}")


def read_labels() -> list[dict]:
    """Return the labeled rows, with ``label_correct`` normalized; exit on an invalid label."""
    with open(LABELS_PATH, encoding=CSV_ENCODING) as f:
        rows = [r for r in csv.DictReader(f, delimiter=CSV_DELIMITER) if r["label_correct"].strip()]
    for r in rows:
        r["label_correct"] = r["label_correct"].strip().lower()
        if r["label_correct"] not in LABEL_SCORES:
            sys.exit(f"Bad label_correct '{r['label_correct']}' for {r['ticker']} {r['date']} (use yes / partial / no)")
    return rows


def weighted_accuracy(rows: list[dict]) -> float | None:
    """Return the accuracy where a partially right answer counts as half."""
    return percent(sum(LABEL_SCORES[r["label_correct"]] for r in rows), len(rows))


def human_eval() -> dict | None:
    """Return the labeled-sample metrics, or None when there are no labels yet."""
    if not LABELS_PATH.exists():
        return None
    rows = read_labels()
    if not rows:
        return None

    typed = [r for r in rows if r["label_type"].strip()]
    return {
        "labeler": LABELER,
        "labeled": len(rows),
        "accuracy_pct": weighted_accuracy(rows),
        "strict_accuracy_pct": percent(sum(r["label_correct"] == "yes" for r in rows), len(rows)),
        "accuracy_by_confidence": {
            level: weighted_accuracy([r for r in rows if r["ai_confidence"] == level]) for level in CONFIDENCE_LEVELS
        },
        "type_accuracy_pct": percent(sum(r["label_type"].strip().lower() == r["ai_type"] for r in typed), len(typed)),
        "errors": [f"{r['ticker']} {r['date']}: {r['notes']}".strip(": ") for r in rows if r["label_correct"] != "yes"],
    }


def cost_summary() -> dict:
    """Return total cost and cost per explanation from the run log.

    Lines without ``kind`` come from explain runs made before the field
    existed. Translation runs count in the total but not per explanation.
    """
    with open(RUNS_LOG, encoding="utf-8") as f:
        runs = [json.loads(line) for line in f]
    explain_runs = [r for r in runs if r.get("kind", "explain") == "explain"]
    explained = sum(r["new_events"] for r in explain_runs)
    explain_cost = sum(r["cost_usd"] for r in explain_runs)
    explain_seconds = sum(r["duration_s"] for r in explain_runs)
    return {
        "runs": len(runs),
        "total_cost_usd": round(sum(r["cost_usd"] for r in runs), 4),
        "translation_cost_usd": round(sum(r["cost_usd"] for r in runs if r.get("kind") == "translate"), 4),
        "cost_per_event_usd": round(explain_cost / explained, 5) if explained else None,
        "avg_seconds_per_event": round(explain_seconds / explained, 1) if explained else None,
    }


def main() -> None:
    """Draw the labeling sample, or compute and save the evaluation summary."""
    sys.stdout.reconfigure(encoding="utf-8")
    events = load_events()
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        create_sample(events)
        return

    summary = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": MODEL,
        "automatic": automatic_checks(events),
        "human": human_eval(),
        "cost": cost_summary(),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
