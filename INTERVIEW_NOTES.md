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

## Numbers
- Events detected: 53 (PETR4 12, VALE3 11, ITUB4 10, MGLU3 13, WEGE3 7)
- Cost per event (Haiku 5.5): ~$0.0002-0.0005, ~1.5k input tokens,
  latency 1.7-4.8 s. Smoke test: 3 events = $0.00116.
- Cost per run: TBD
- Eval accuracy: TBD

## Limitations

## Next steps
- CVM filings, pytest suite, prompt A/B comparison, more tickers, Telegram alerts
