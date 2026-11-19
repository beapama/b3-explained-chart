# Progress

## Done
- [x] 1. Setup: folders, requirements, .env.example, config
- [x] 2. Prices: `python -m src.prices` -> data/prices/*.json (248 days each)
- [x] 3. Detection: `python -m src.detect` -> 53 events (z>=2.5, 60d window)

## Current step
- 1. Setup — waiting for local confirmation (venv + install)

## Next
2. Prices · 3. Detection · 4. News · 5. AI explanation · 6. Cache + backfill
7. Eval · 8. Site · 9. GitHub Actions · 10. README

## Open issues
- MGLU3 2026-10-26: -58% in one day (open already -50%). Election-related
  crash (Ibov -13.9%, runoff on 2026-10-25) or an unadjusted corporate event
  (e.g. reverse split / offering)? Check with the news step.
- Real outliers (election days, |z| up to 9) inflate the rolling std for the
  next 60 days, making the detector less sensitive right after a crash.
