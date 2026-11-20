# Interview notes

## Architecture in 5 lines
(to be filled as the pipeline takes shape)

## Key decisions and trade-offs
- **Single `src/config.py`** for universe, paths and parameters: every step
  (prices, detection, news, AI, site) reads the same source of truth.
- **Data committed to the repo** (`data/`): the static site reads JSON files
  directly, so no database or backend is needed. Git history doubles as an
  audit log of what the AI said and when.
- **Secrets**: `.env` locally (gitignored, `.env.example` documents the
  variable), GitHub Secrets in CI. `load_dotenv` is a no-op in CI.
- **Adjusted prices** (`auto_adjust=True`): dividends/splits would otherwise
  show up as fake drops and be flagged as "strong moves".
- **Prices saved as JSON in lightweight-charts shape** (`time/open/high/low/
  close`): the site plots the file with zero transformation.
- **Full re-download each run** instead of incremental: 6 free requests, and
  it catches retroactive adjustments. Trade-off: slightly more bandwidth,
  much less code.
- **Known risk**: yfinance is an unofficial Yahoo scraper; it can break or
  rate-limit. Fine for an MVP; a paid data vendor would replace it in prod.

- **Rolling z-score instead of a fixed % threshold**: each stock is judged
  against its own volatility. MGLU3 needs ~8% to be "strong", ITUB4 ~3.5%.
  A fixed 5% cut would flood MGLU3 and miss the banks.
- **Baseline uses only past days (`shift(1)`)**: today's move must not
  inflate its own std (look-ahead bias, and it would hide the event).
- **60-day window, threshold 2.5**: tested 20/60 days x 2.0/2.5/3.0. 20 days
  gives a noisy std; 2.0 gives ~95 events (too many to explain/label); 3.0
  only ~15. 60/2.5 -> 53 events, ~1 per stock per month.
- **Warm-up**: download 100 extra calendar days so the window is full on
  the first day of the 12-month period.
- **Market vs stock**: "market" if the Ibovespa's own z >= 2 in the same
  direction; also store excess return (stock - Ibov). Simple alternative to
  a beta-adjusted (CAPM) abnormal return; beta is a next step.
- **Normality caveat**: returns have fat tails, so z=2.5 is not "1% chance";
  it is a relative ranking of unusual days, not a probability.
- **Google News RSS** for context: free, no key, supports `after:`/`before:`
  date operators, Brazilian outlets (Valor, InfoMoney, Estadão). Trade-off:
  unofficial endpoint, only headlines (no article body), redirect URLs. Paid
  alternative: a news API with full text.
- **News window = previous trading day -> day after the event**: a Monday
  move is usually caused by weekend news (the 2026-10-26 crash came from the
  Sunday runoff election). Day-after catches "why it fell" recaps.
- **Query = name + market terms** (`"Petrobras" (ações OR PETR4 OR Ibovespa
  OR bolsa)`): the plain name returned job contests and sponsorships.
- **Market-scope events also search "Ibovespa"** for macro context.
- **Dedupe by normalized headline**, max 8 per event: same story syndicated
  by several outlets; 8 keeps the prompt short and cheap.
- **Detector sanity check paid off**: MGLU3 -58% looked like bad data; news
  confirmed it was real (biggest drop since 1994 after the election).
- **Model: Claude Haiku 5.5** ($0.10 / $0.50 per M tokens): the task is
  short reading comprehension over ~8 headlines, not deep reasoning. Swap
  is one constant in config if eval shows quality issues.
- **Structured output with Pydantic** (`messages.parse`): the API is
  constrained to the schema (enums for type/confidence) and the SDK
  validates on our side. No regex parsing of free text.
- **Model cites source NUMBERS, not URLs**: we map ids -> URLs in code, so a
  hallucinated or mistyped link is impossible by construction; ids outside
  the list are dropped and logged (`invalid_source_ids`) for the eval.
  Also saves tokens (Google redirect URLs are ~200 chars).
- **Explicit "no clear explanation" path** + `type: "unknown"`: the
  prompt makes abstaining a valid answer, so the model is not pushed to
  invent a cause when headlines are irrelevant. (Added "unknown" to the
  company/sector/macro enum for that case.)
- **"Use only the headlines"**: grounding rule, so explanations are
  auditable against the sources shown on the site. Limitation: headlines
  only, no article body.
- **Detector context in the prompt** (return, z, Ibovespa return, scope):
  helps the model choose macro vs company (e.g. -58% with Ibov -14%).
- **Every call logs tokens, cost and latency** in `meta` -> cost per run
  and eval numbers come from real data, not estimates.
- **Cache keyed by (ticker, date)** in `data/events/{TICKER}.json`: an
  event already explained is never sent to the API again. Daily cost is
  proportional to NEW events (0-2 per day), not to history size.
- **Save after every event**: the backfill can crash or be stopped and
  resumes where it left off; failed events are simply retried next run.
- **Store the news the model saw** next to its answer: makes every
  explanation auditable and lets the eval check citations offline.
- **`--dry-run`** prints pending events and estimated cost before spending.
- **Run log** (`data/eval/runs.jsonl`): one line per run with new events,
  failures, cost and duration -> real cost numbers for the README.
- **Trade-off of the cache**: if the prompt or model changes, old events
  keep the old explanation. Fix = delete the file (or add a prompt version
  to the cache key) and re-run; cheap at ~$0.03 per full backfill.
- **Secret hygiene incident**: a key ended up in `.env.example` and was
  committed locally; caught before push by reviewing the diff, commit
  rewritten and objects purged. Lesson: scan staged diffs for `sk-ant-`.
- **Failure analysis after the backfill: retrieval, not generation.**
  13/53 events came back "no clear explanation". Reading the inputs showed
  that on market-wide days the company query filled all 8 slots and the
  Ibovespa news (where the macro cause is) were cut. Example: ITUB4 -13.7%
  on election day got 5/8 headlines about an unrelated acquisition; the
  model correctly refused to invent a cause. Fix: reserve 4/8 slots for
  Ibovespa news on market-scope events. Lesson: in RAG-style systems, look
  at what the model was given before blaming the model.
- **Iteration 2 of retrieval**: the quota alone gave mixed results (13 -> 12
  unexplained; ITUB4 election day fixed, but ITUB4 2025-12-05 regressed
  because the cause headline had come through the company query and was
  now cut). Plain "Ibovespa" ranks generic "record high" pieces first.
  Fix: market query with direction words `(Ibovespa OR bolsa) (cai OR
  queda OR despenca OR sobe OR dispara OR alta)` and 10 headlines (5+5).
- **Non-determinism, two sources**: Google News returns different results
  on each call, and the model may label borderline days differently
  (ITUB4 2026-07-10: sector -> macro between runs). That is why the news
  the model saw is stored with each event, and why the eval must be run on
  the stored inputs, not re-fetched ones.
- **Data quality guard**: Yahoo returned the latest day with volume but
  NaN prices when run around midnight. NaN rows are dropped (logged) and
  `json.dumps(allow_nan=False)` fails loudly, since NaN is invalid JSON and
  would break the site. Implication for CI: schedule the job in the
  evening, not around midnight.
- **Eval in two layers**: (1) automatic checks on all 53 events, free and
  re-runnable (grounding: every cited URL is in the list we provided;
  consistency: abstentions have no sources and type "unknown", real
  answers cite >= 1 source; detector-vs-AI agreement on market days);
  (2) human labels on a fixed, stratified sample of 15 (seed 42; 4 macro,
  4 company, 3 sector, 4 unknown) -> accuracy and calibration by
  confidence. Runs on stored inputs, so it is reproducible.
- **Why stratified**: a random 15 would be mostly macro; stratifying makes
  sure abstentions ("unknown") are also judged (was abstaining right?).
- **Grounding is 100% by construction** (numbered sources), so the check is
  a regression test, not a discovery. The real quality question (is the
  cause right?) needs a human -> the hand labels.
- **Labels came from a stronger model (LLM-as-judge), not by hand**:
  faster, but a judge can share blind spots with the model it grades.
  Mitigations: different, larger model; per-row written rationale so a
  human can audit each label; the site states who labeled. Honest framing
  in the interview: "LLM-judged, human-reviewed", never "hand-labeled".
- **Main error pattern**: on stock-specific days with weak headlines the
  model gives a low-confidence "reach" (VALE3: "new favorable wind",
  "foreign investor raised stake") instead of abstaining. Abstentions
  themselves were all correct. Next step: rule "if confidence would be
  low, abstain", then re-measure on the same 15 events.
- **Calibration is useful**: high-confidence answers were right 93% of the
  time. The site shows the confidence badge so users can weigh answers.
- **Static site, no framework, no build tool**: one HTML + CSS + JS file
  reading JSON. GitHub Pages serves it for free; nothing to run or patch.
  `src/build_site.py` assembles `_site/` (site + only the data the browser
  needs) - same command locally and in CI, so what I test is what ships.
- **lightweight-charts pinned to 5.0.9** (exact version in the CDN URL): a
  new major release could change the API and silently break the page.
- **Chart design**: neutral ink price line so color means only one thing
  (event type). Marker color = type, marker shape = direction (▲/▼), marker
  letter M/S/E/? = type again, so identity never depends on color alone
  (colorblind users, print). Palette: first 3 slots of a validated
  categorical palette, checked with a colorblind-simulation script in light
  and dark mode; dark mode has its own selected colors, not an inversion.
- **Event table = accessible view of the markers** and the mobile-friendly
  way to select an event (markers are small touch targets).
- **News text is untrusted input**: rendered with `textContent`, links
  limited to http(s), `rel="noopener noreferrer"` -> no XSS from a feed.
- **Eval is on the page**, including who labeled the sample, so a visitor
  sees the limits, not just the claims.
- **Checked by rendering** (headless Edge screenshots, desktop/mobile,
  light/dark): caught a mobile overflow (CSS grid items do not shrink below
  their content by default -> `min-width: 0`) and an axis label bug.
- **Redesign ("Pregão Explicado")**: financial-newspaper graphics style.
  The headline is the finding, computed from the data per ticker ("PETR4
  teve 12 dias de movimento forte em 12 meses; 6 vieram de notícias do
  setor"), then a ruled row of key figures (close, 12-month change vs
  Ibovespa, biggest marked up/down day), then the chart with the selected
  event called out by a leader line and the explanation in a narrow column
  beside it. Literata serif; cherry palette chosen by me (wine #621027
  masthead, raspberry #D52A63 accent, rose #E59693 tints).
- **Brand palette vs. data colors**: the cherry palette is three shades of
  one red, which cannot tell event types apart (especially for colorblind
  users). So the brand colors go on the page chrome, and the markers use
  raspberry plus two hues that fit the photo (stem green, plum), validated
  with the colorblind-simulation script in light and dark mode.
- **Own HTML pins instead of the library's markers**: the library draws
  tiny letters in the marker color (unreadable). Pins are 22px discs with
  a white letter, a tip showing direction, a 40px tap area and keyboard
  focus. Trade-off: I position them myself on scroll/zoom/resize.
  Light/dark follows the system setting (no toggle button).

## Numbers
- Events detected: 53 (PETR4 12, VALE3 11, ITUB4 10, MGLU3 13, WEGE3 7)
- Cost per event (Haiku 5.5): ~$0.0002-0.0005, ~1.5k input tokens,
  latency 1.7-4.8 s. Smoke test: 3 events = $0.00116.
- Backfill run 1: 53 events, 0 failures, $0.018 total, 264 s (mostly the
  1 s politeness delay between Google News requests).
- Retrieval iterations ("no clear explanation" out of 53):
  v1 13 (company news filled all slots) -> v2 12 (4/8 quota) -> v3 9
  (direction-word market query, 5/10 quota). Market-scope events:
  5/22 -> 1/22 unexplained. Remaining 8 are stock-specific days with few
  or irrelevant headlines (e.g. MGLU3 2026-02-12 had 1 headline).
- Final backfill: 53 events = 22 macro, 14 company, 8 sector, 9 unknown;
  confidence 25 high / 15 medium / 13 low; 0 invalid source ids.
- Total API spend so far (backfill + 2 re-runs of 22 market events): $0.035.
- Cost per daily run: ~$0.0004 per new event; typical day has 0-2 events
  -> well under $0.03/month in API cost.
- Automatic eval: 133 sources cited, 100% grounded, 0 invalid ids, 0
  inconsistent answers; 86.4% of market-scope events labeled macro by the
  AI (independent signals agreeing).
- Cost per explanation: $0.00036 (97 explanations incl. re-runs).
- Labeled eval (15 events, LLM-as-judge with Claude Opus 5.5 as labeler,
  pending human review): accuracy 76.7% (partial = 0.5), strict 66.7%,
  type accuracy 86.7%. By confidence: high 92.9% (n=7), medium 50% (n=2),
  low 66.7% (n=6). Abstentions: 5/5 judged correct.

## Limitations
- Explanations use headlines only (no article body); Google News is an
  unofficial source and results vary per call.
- 9/53 events have no explanation; most are stock-specific days with few
  headlines. Low-confidence answers are often weak guesses.
- Eval sample is small (15) and LLM-judged; numbers are indicative.
- Market vs stock split uses a simple Ibovespa z-score, not beta.

## Next steps
- CVM filings, pytest suite, prompt A/B comparison, more tickers, Telegram alerts
