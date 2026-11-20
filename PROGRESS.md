# Progress

## Done
- [x] 1. Setup: folders, requirements, .env.example, config
- [x] 2. Prices: `python -m src.prices` -> data/prices/*.json (+100 warm-up days)
- [x] 3. Detection: `python -m src.detect` -> 53 events (|z| >= 2.5, 60-day window)
- [x] 4. News: `python -m src.news` -> Google News RSS, up to 10 deduped headlines/event
- [x] 5. AI explanation: `python -m src.explain` -> Claude Haiku 5.5, structured output, ~$0.0004/event
- [x] 6. Cache + backfill: `python -m src.pipeline` -> 53 events in data/events,
  9 "no clear explanation" after 3 retrieval iterations, $0.035 total spend
- [x] 7. Mini eval: `python -m src.evaluate` -> 100% grounded; 15 events labeled
  by LLM-as-judge (accuracy 76.7%, strict 66.7%). Pending: Beatriz reviews
  data/eval/labels.csv, then updates LABELER in src/evaluate.py.

- [x] 8. Site "Pregão Explicado": `python -m src.build_site` -> _site/ (static page,
  cherry palette, HTML pins, eval section). Checked desktop/mobile, light/dark.

- [x] 9. GitHub Actions: daily update + Pages deploy, both jobs green (push and
  manual run). Live: https://beapama.github.io/b3-explained-chart/
- [x] 10. README: what it is, live link, screenshots, mermaid diagram, eval, cost,
  limitations, next steps.

## Current step
- Done. Optional before the interview: review data/eval/labels.csv, then set
  LABELER in src/evaluate.py to "...revisado por humano" and re-run the eval.

## Next
- (out of scope, see README next steps)

## Open issues
- ~~MGLU3 2026-10-26 -58%: data error?~~ Resolved: real move, "biggest daily
  drop since 1994 after Lula's reelection" (Valor). Retail stocks crashed.
- Incident: API key was pasted into .env.example and committed locally
  (never pushed). Commit rewritten, objects purged, history scanned clean.
  TODO (optional): local pre-commit hook that blocks `sk-ant-` strings.
- Fixed: VS Code injected an empty ANTHROPIC_API_KEY into the terminal;
  `load_dotenv(override=True)` makes .env win locally.
- Fixed: on phones, pins and callout were placed before the chart finished
  resizing (stale coordinates). Now re-placed after the chart redraws
  (double requestAnimationFrame + timeScale().subscribeSizeChange).
- Fixed: Yahoo returns NaN prices for the latest day around midnight ->
  rows dropped + `allow_nan=False`. Schedule CI in the evening (step 9).
- Google News links are news.google.com redirect URLs (open fine in a
  browser, but are not the publisher URL).
- Results are non-deterministic (Google results vary per call; model may
  label borderline days differently). Eval must use the stored news.
- 8 stock-specific events remain unexplained: few/irrelevant headlines.
- Real outliers (election days, |z| up to 9) inflate the rolling std for the
  next 60 days, making the detector less sensitive right after a crash.
