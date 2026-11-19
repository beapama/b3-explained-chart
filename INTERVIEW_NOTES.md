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

## Numbers
- Events detected: TBD
- Cost per run: TBD
- Eval accuracy: TBD

## Limitations

## Next steps
- CVM filings, pytest suite, prompt A/B comparison, more tickers, Telegram alerts
