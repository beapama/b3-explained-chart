# Progress

## Done
- [x] 1. Setup: folders, requirements, .env.example, config
- [x] 2. Prices: `python -m src.prices` -> data/prices/*.json (248 days each)
- [x] 3. Detection: `python -m src.detect` -> 53 events (z>=2.5, 60d window)
- [x] 4. News: `python -m src.news` -> Google News RSS, up to 8 deduped articles/event
- [x] 5. AI explanation: `python -m src.explain` -> 3/3 sample events correct type, valid sources, ~$0.0004/event

## Current step
- 1. Setup — waiting for local confirmation (venv + install)

## Next
2. Prices · 3. Detection · 4. News · 5. AI explanation · 6. Cache + backfill
7. Eval · 8. Site · 9. GitHub Actions · 10. README

## Open issues
- ~~MGLU3 2026-10-26 -58%: data error?~~ Resolved: real move, "biggest daily
  drop since 1994 after Lula's reelection" (Valor). Retail stocks crashed.
- Fixed: VS Code injected an empty ANTHROPIC_API_KEY into the terminal;
  `load_dotenv(override=True)` makes .env win locally.
- Google News links are news.google.com redirect URLs (open fine in a
  browser, but are not the publisher URL).
- Some articles in the list are context, not cause (e.g. "Petrobras in
  Genial's portfolio"); the model must pick the relevant ones.
- Real outliers (election days, |z| up to 9) inflate the rolling std for the
  next 60 days, making the detector less sensitive right after a crash.
