"""Step 7: mini evaluation. No API calls: everything runs on the stored events.

Two parts:
1. Automatic checks on ALL events (grounding, schema/consistency, scope vs type).
2. Human labels on a fixed stratified sample (~15 events) -> accuracy.

Usage:
    python -m src.evaluate sample   # create data/eval/labels.csv to fill by hand
    python -m src.evaluate          # compute data/eval/summary.json (site reads it)
"""
import csv
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone

from src.config import EVAL_DIR, EVENTS_DIR, MODEL, TICKERS
from src.explain import NO_EXPLANATION

LABELS_PATH = EVAL_DIR / "labels.csv"
SUMMARY_PATH = EVAL_DIR / "summary.json"
SAMPLE_PER_TYPE = {"macro": 4, "company": 4, "sector": 3, "unknown": 4}  # 15 events
SEED = 42  # fixed: the sample is reproducible
# Who produced the labels. Be honest here: it is shown on the site. Kept as data
# (not text) so the site can phrase it in Portuguese or English.
# Set human_reviewed to True only after a person has checked labels.csv.
LABELER = {"model": "Claude Opus 5.5", "method": "llm-as-judge", "human_reviewed": False}


def load_events() -> list[dict]:
    events = []
    for ticker in TICKERS:
        path = EVENTS_DIR / f"{ticker}.json"
        if path.exists():
            events += [{"ticker": ticker, **e} for e in json.loads(path.read_text(encoding="utf-8"))]
    return events


# ---------- Part 1: automatic checks ----------

def automatic_checks(events: list[dict]) -> dict:
    cited = grounded = 0
    inconsistent = []
    for e in events:
        ai = e["ai"]
        provided = {n["url"] for n in e["news"]}
        for s in ai["sources"]:
            cited += 1
            grounded += s["url"] in provided  # cited source must be one we gave it

        abstained = ai["short_reason"] == NO_EXPLANATION
        # Abstention must be clean; a real explanation must cite something.
        ok = (ai["type"] == "unknown" and not ai["sources"]) if abstained else bool(ai["sources"])
        if not ok:
            inconsistent.append(f"{e['ticker']} {e['date']}")

    market = [e for e in events if e["scope"] == "market"]
    explained = [e for e in events if e["ai"]["short_reason"] != NO_EXPLANATION]
    return {
        "events": len(events),
        "explained": len(explained),
        "no_clear_explanation": len(events) - len(explained),
        "sources_cited": cited,
        "sources_grounded_pct": round(100 * grounded / cited, 1) if cited else None,
        "invalid_source_ids": sum(len(e["ai"]["meta"]["invalid_source_ids"]) for e in events),
        "inconsistent_answers": inconsistent,
        # Detector says "whole market moved" -> does the AI agree it is macro?
        "market_scope_labeled_macro_pct": round(
            100 * sum(e["ai"]["type"] == "macro" for e in market) / len(market), 1) if market else None,
        "by_type": dict(Counter(e["ai"]["type"] for e in events)),
        "by_confidence": dict(Counter(e["ai"]["confidence"] for e in events)),
    }


# ---------- Part 2: human labels ----------

def create_sample(events: list[dict]) -> None:
    if LABELS_PATH.exists():
        sys.exit(f"{LABELS_PATH} already exists; delete it to draw a new sample.")
    rng = random.Random(SEED)
    sample = []
    for typ, n in SAMPLE_PER_TYPE.items():
        pool = [e for e in events if e["ai"]["type"] == typ]
        sample += rng.sample(pool, min(n, len(pool)))
    sample.sort(key=lambda e: (e["ticker"], e["date"]))

    # utf-8-sig + ";" so Excel (pt-BR) opens it with accents and columns right.
    with open(LABELS_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ticker", "date", "return", "ibov_return", "ai_type", "ai_confidence",
                    "ai_short_reason", "ai_explanation", "headlines_given",
                    "label_correct", "label_type", "notes"])
        for e in sample:
            headlines = " | ".join(f"[{i}] {n['title']}" for i, n in enumerate(e["news"], 1))
            w.writerow([e["ticker"], e["date"], f"{e['return']:+.2%}", f"{e['ibov_return']:+.2%}",
                        e["ai"]["type"], e["ai"]["confidence"], e["ai"]["short_reason"],
                        e["ai"]["explanation"], headlines, "", "", ""])
    print(f"Wrote {len(sample)} events to {LABELS_PATH}")


def human_eval() -> dict | None:
    if not LABELS_PATH.exists():
        return None
    with open(LABELS_PATH, encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f, delimiter=";") if r["label_correct"].strip()]
    if not rows:
        return None

    score = {"yes": 1.0, "partial": 0.5, "no": 0.0}
    for r in rows:
        r["label_correct"] = r["label_correct"].strip().lower()
        if r["label_correct"] not in score:
            sys.exit(f"Bad label_correct '{r['label_correct']}' for {r['ticker']} {r['date']} "
                     f"(use yes / partial / no)")

    def acc(subset):
        return round(100 * sum(score[r["label_correct"]] for r in subset) / len(subset), 1) if subset else None

    typed = [r for r in rows if r["label_type"].strip()]
    return {
        "labeler": LABELER,
        "labeled": len(rows),
        "accuracy_pct": acc(rows),  # partial counts as half
        "strict_accuracy_pct": round(100 * sum(r["label_correct"] == "yes" for r in rows) / len(rows), 1),
        # Calibration: high-confidence answers should be right more often.
        "accuracy_by_confidence": {c: acc([r for r in rows if r["ai_confidence"] == c])
                                   for c in ("high", "medium", "low")},
        "type_accuracy_pct": round(100 * sum(r["label_type"].strip().lower() == r["ai_type"]
                                             for r in typed) / len(typed), 1) if typed else None,
        "errors": [f"{r['ticker']} {r['date']}: {r['notes']}".strip(": ")
                   for r in rows if r["label_correct"] != "yes"],
    }


def cost_summary() -> dict:
    runs = [json.loads(line) for line in open(EVAL_DIR / "runs.jsonl", encoding="utf-8")]
    # Older lines have no "kind": they are explain runs. Translation runs are
    # counted in the total but not in the cost per explanation.
    explain = [r for r in runs if r.get("kind", "explain") == "explain"]
    explained = sum(r["new_events"] for r in explain)
    explain_cost = sum(r["cost_usd"] for r in explain)
    return {
        "runs": len(runs),
        "total_cost_usd": round(sum(r["cost_usd"] for r in runs), 4),
        "translation_cost_usd": round(sum(r["cost_usd"] for r in runs if r.get("kind") == "translate"), 4),
        "cost_per_event_usd": round(explain_cost / explained, 5) if explained else None,
        "avg_seconds_per_event": round(sum(r["duration_s"] for r in explain) / explained, 1) if explained else None,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    events = load_events()
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        create_sample(events)
        return

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL,
        "automatic": automatic_checks(events),
        "human": human_eval(),
        "cost": cost_summary(),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
