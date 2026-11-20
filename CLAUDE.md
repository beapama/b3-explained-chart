# Project: The self-explaining stock chart (FAST MODE — deadline Tuesday)

## Who I am
I'm Beatriz, Computer Engineering student at Poli-USP, with backend Python and
SQL experience in treasury (BTG, QI Tech). I'm new to LLM APIs, GitHub Actions,
GitHub Pages and front-end. I'm presenting this project in a GenAI internship
interview on Tuesday.

## Goal
A website with daily price charts of B3 stocks where AI marks the days with
strong moves and explains, on the chart itself, what happened, citing sources.
Every business day after market close, an automation detects new moves,
generates the explanations and updates the site on its own.

## How to work with me (IMPORTANT)
- Time is short: YOU write the code. My job is to understand it well enough to
  defend every decision in an interview.
- Work one step at a time. After each step:
  1. Explain in up to 5 lines (in Portuguese) what was done and WHY.
  2. Highlight any design decision or trade-off I should be able to explain.
  3. Ask me to run it and confirm it works before moving on.
- If I ask "por quê?", answer as if an interviewer were asking.
- Code, comments, names and commits in English. Talk to me in Portuguese.
- Keep PROGRESS.md updated (steps done, current step, open issues).
- Keep INTERVIEW_NOTES.md updated with: architecture in 5 lines, key decisions
  and trade-offs, numbers (events, cost per run, eval accuracy), limitations
  and next steps. This file is my interview prep.
- API keys only in .env (local) or GitHub Secrets. Never commit them.
- Warn me before anything that may generate many API calls.
- Prefer the simplest thing that works. No over-engineering.

## Scope (MVP — do not add more)
Universe: PETR4, VALE3, ITUB4, MGLU3, WEGE3 + Ibovespa. Last 12 months.

1. Setup: repo structure, venv, requirements, .env, .gitignore.
2. Prices: daily history via yfinance (.SA tickers, adjusted prices),
   saved to data/prices/.
3. Strong-move detection: daily return z-score over a rolling window, plus
   comparison with Ibovespa that day (stock-specific vs market-wide move).
4. Context: news for each event date via Google News RSS with date filters.
   Dedupe, limit per event.
5. AI explanation with the Claude API: system prompt + validated JSON output
   (short_reason, explanation, type: company/sector/macro,
   confidence: high/medium/low, sources: only URLs I provided).
   If sources don't explain the move, answer "no clear explanation".
   Use a small, cheap model.
6. Cache in data/events/{ticker}.json — never call the API twice for the same
   event. Run the 12-month backfill.
7. Mini eval: automatic check that every cited source exists in the provided
   list + I label ~15 events by hand and we compute accuracy. Log cost and
   time per run. Save results to show on the site.
8. Static site (GitHub Pages): reads the JSONs, chart with lightweight-charts
   (pinned version), ticker selector, markers colored by type, click a marker
   to see reason, explanation, confidence badge and source links; a small
   "How the AI is evaluated" section; light/dark mode; works on mobile.
9. GitHub Actions: business days after market close (mind UTC), detect only
   new events, explain, commit data, deploy the site.
10. README: what it is, live link, GIF/screenshot, architecture diagram,
    evaluation, monthly cost, limitations, next steps.

## Extension after the MVP: English version (for recruiters)
Same site, same content, in English, with a language switch. One site, not
two copies: the page reads the language and swaps texts.

11. English version of the site:
    a. UI texts: move every fixed text (masthead, legend, table headers,
       method section, footer, buttons) into one dictionary per language
       (pt, en) in site/app.js; no text hard-coded in the HTML that the
       switch cannot reach.
    b. Generated texts: the per-ticker finding headline and the figures row
       get one template per language; numbers, percentages, currency and
       dates formatted per locale (pt-BR: R$ 43,17 / 4 nov 2026;
       en: R$ 43.17 / Nov 4, 2026). Keep BRL as the currency.
    c. AI texts: add short_reason_en and explanation_en to each event.
       New events: ask for both languages in the same API call (extend the
       Pydantic schema, one call per event, no extra cost per event).
       Existing events: one-time script that translates the cached
       Portuguese fields with Claude Haiku, without re-explaining (the
       Portuguese text, its sources and the eval stay unchanged). Warn
       before running it (~53 calls, estimate the cost first).
    d. News headlines stay in Portuguese (they are the original sources);
       in English, show a small "(headline in Portuguese)" note.
    e. Eval section and labeler text in both languages (summary.json stays
       language-neutral; the site maps it to text).
    f. Language switch: a PT | EN toggle in the masthead. Choice order:
       URL (?lang=en, so the README and the CV can link straight to the
       English page) > saved choice (localStorage) > browser language >
       Portuguese. Update <html lang>, the page title and the meta
       description when it changes; keep the selected ticker and event.
    g. Check by rendering both languages on desktop and phone, light and
       dark; no layout break with the longer/shorter strings.
    h. README: link to the English page (…/?lang=en) next to the live link;
       update INTERVIEW_NOTES with the decisions (one site with a
       dictionary vs two sites; translate cached events vs re-explain).

Out of scope (list as next steps in README): CVM filings, pytest suite,
prompt A/B comparison, more tickers, Telegram alerts.

Start with step 1.