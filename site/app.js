// Pregão Explicado / B3 Moves, Explained: reads the static JSON written by the
// Python pipeline. No framework, no build step. One page, two languages: every
// text the user sees comes from STR below, so the PT | EN switch reaches all of it.
// News text is untrusted, so the DOM is built with textContent only.
{
  const { createChart, LineSeries, ColorType, CrosshairMode } = LightweightCharts;

  // ---------- language ----------
  const LOCALE = { pt: "pt-BR", en: "en-US" };
  const STR = {
    pt: {
      brand: "Pregão Explicado",
      tagline: "Os dias de movimento forte de cinco ações da B3, com o motivo de cada um segundo as notícias.",
      metaDesc: "Os dias de movimento forte de cinco ações da B3 nos últimos 12 meses, com o motivo de cada um segundo as notícias.",
      tickersLabel: "Escolha a ação",
      loading: "Carregando…",
      loadError: "Não foi possível carregar os dados.",
      months: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
      dayMonth: (d, m) => `${d} ${m}`,
      dayYear: (d, m, y) => `${d} ${m} ${y}`,
      types: {
        macro: { letter: "M", name: "Mercado inteiro", many: "acompanharam o mercado inteiro" },
        sector: { letter: "S", name: "Setor", many: "vieram de notícias do setor" },
        company: { letter: "E", name: "Empresa", many: "vieram de notícias da própria empresa" },
        unknown: { letter: "?", name: "Sem explicação clara", many: "" },
      },
      conf: { high: "alta", medium: "média", low: "baixa" },
      legendHint: "A ponta do marcador indica alta (para cima) ou queda (para baixo). Clique num marcador para ler o motivo.",
      chartAria: "Preço de fechamento nos últimos 12 meses com os dias de movimento forte marcados",
      finding: (t, n, top) => {
        if (!n) return `${t} não teve dias de movimento forte nos últimos 12 meses.`;
        const head = `${t} teve ${n} ${n === 1 ? "dia" : "dias"} de movimento forte em 12 meses`;
        return top ? `${head}; ${top.count} ${top.many}.` : `${head}.`;
      },
      fig: { close: "Fechamento", change: "Em 12 meses", up: "Maior alta marcada", down: "Maior queda marcada" },
      noEvents: "Nenhum dia marcado neste período.",
      when: (date, i, n) => `${date}, dia ${i} de ${n}`,
      ibovSame: (x) => `Ibovespa ${x} no mesmo dia`,
      unknownTitle: "As notícias não explicam este movimento",
      unknownShort: "Sem explicação clara",
      kind: (name, conf) => `${name}, confiança ${conf}`,
      sourcesTitle: (c, n) => `Fontes citadas (${c} de ${n} manchetes lidas)`,
      noSources: "Nenhuma das manchetes encontradas explica o movimento.",
      aiNote: (model) => `Texto escrito por IA (${model}) a partir das manchetes acima. Pode conter erros.`,
      prev: "← Anterior", next: "Próximo →",
      tipDay: (p, r) => `${p} no dia. ${r}`,
      eventsTitle: (t) => `Todos os dias marcados de ${t}`,
      head: ["Data", "Ação", "Ibovespa", "Tipo", "Motivo", "Confiança"],
      evalTitle: (n, acc, high) => `Em ${n} explicações conferidas, ${acc} estavam certas; com confiança alta, ${high}`,
      evalTitleDefault: "Como a IA é conferida",
      tiles: {
        grounded: ["Fontes conferidas", (n) => `${n} citações, nenhuma inventada`],
        acc: ["Acertos na amostra", (s) => `${s} sem contar parciais`, "pendente"],
        explained: ["Dias explicados", (a, b) => `${a} de ${b}`, (n) => `${n} sem explicação clara`],
        cost: ["Custo por explicação", (t) => `${t} no total`],
      },
      m1h: "Como os dias são escolhidos",
      m1p: "Um dia entra no gráfico quando a variação da ação foge muito do normal dela: mais de 2,5 desvios-padrão em relação aos 60 pregões anteriores. Assim, 4% é muito para o Itaú e pouco para a Magazine Luiza. A comparação com o Ibovespa no mesmo dia separa o que foi da ação do que foi do mercado.",
      m2h: "Como a IA explica",
      m2p: (model) => `Para cada dia buscamos até 10 manchetes no Google News, do pregão anterior ao dia seguinte. O modelo ${model} lê só essas manchetes e cita as que usou. Quando elas não explicam o movimento, a resposta é “sem explicação clara”, e não um palpite.`,
      m3h: "Como conferimos",
      m3p: "O modelo cita as fontes pelo número que cada manchete tem na lista, e o código troca o número pelo link. Por isso nenhuma fonte pode ser inventada.",
      m3pHuman: (n, who) => `O modelo cita as fontes pelo número que cada manchete tem na lista, e o código troca o número pelo link, então nenhuma fonte pode ser inventada. Também sorteamos ${n} dias e julgamos cada explicação como certa, parcial ou errada. Quem julgou: ${who}. O erro mais comum é arriscar um motivo fraco, com confiança baixa, em vez de dizer que as notícias não explicam.`,
      labeler: (l) => `${l.model} como juiz (LLM-as-judge); revisão humana ${l.human_reviewed ? "feita" : "pendente"}`,
      limits: "Limites: a IA lê só manchetes, não o texto das matérias. O Google News devolve resultados um pouco diferentes a cada busca. A amostra conferida é pequena. Nada aqui é recomendação de investimento.",
      footer: (d) => `Preços ajustados do Yahoo Finance e manchetes do Google News, atualizados todo dia útil depois do fechamento. Última atualização: ${d}. `,
      code: "Código no GitHub",
    },
    en: {
      brand: "B3 Moves, Explained",
      tagline: "The days five Brazilian stocks moved sharply, and why, according to the news.",
      metaDesc: "The days of unusually strong moves in five B3 (Brazilian exchange) stocks over the last 12 months, each explained from the news by AI.",
      tickersLabel: "Choose a stock",
      loading: "Loading…",
      loadError: "Could not load the data.",
      months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      dayMonth: (d, m) => `${m} ${d}`,
      dayYear: (d, m, y) => `${m} ${d}, ${y}`,
      types: {
        macro: { letter: "M", name: "Whole market", many: "followed the whole market" },
        sector: { letter: "S", name: "Sector", many: "came from sector news" },
        company: { letter: "C", name: "Company", many: "came from company news" },
        unknown: { letter: "?", name: "No clear explanation", many: "" },
      },
      conf: { high: "high", medium: "medium", low: "low" },
      legendHint: "The marker's tip points up for a rise and down for a fall. Click a marker to read why.",
      chartAria: "Closing price over the last 12 months with the days of strong moves marked",
      finding: (t, n, top) => {
        if (!n) return `${t} had no days of strong moves in the last 12 months.`;
        const head = `${t} had ${n} ${n === 1 ? "day" : "days"} of strong moves in 12 months`;
        return top ? `${head}; ${top.count} ${top.many}.` : `${head}.`;
      },
      fig: { close: "Close", change: "Last 12 months", up: "Biggest marked rise", down: "Biggest marked fall" },
      noEvents: "No days marked in this period.",
      when: (date, i, n) => `${date}, day ${i} of ${n}`,
      ibovSame: (x) => `Ibovespa ${x} the same day`,
      unknownTitle: "The news does not explain this move",
      unknownShort: "No clear explanation",
      kind: (name, conf) => `${name}, ${conf} confidence`,
      sourcesTitle: (c, n) => `Sources cited (${c} of ${n} headlines read, in Portuguese)`,
      noSources: "None of the headlines found explains the move.",
      aiNote: (model) => `Written by AI (${model}) from the headlines above, then translated to English. It may contain errors.`,
      prev: "← Previous", next: "Next →",
      tipDay: (p, r) => `${p} that day. ${r}`,
      eventsTitle: (t) => `Every marked day for ${t}`,
      head: ["Date", "Stock", "Ibovespa", "Type", "Reason", "Confidence"],
      evalTitle: (n, acc, high) => `Of ${n} explanations checked, ${acc} were right; ${high} when the model was confident`,
      evalTitleDefault: "How the AI is checked",
      tiles: {
        grounded: ["Sources verified", (n) => `${n} citations, none invented`],
        acc: ["Right in the sample", (s) => `${s} not counting partials`, "pending"],
        explained: ["Days explained", (a, b) => `${a} of ${b}`, (n) => `${n} with no clear explanation`],
        cost: ["Cost per explanation", (t) => `${t} in total`],
      },
      m1h: "How the days are picked",
      m1p: "A day is marked when the stock's return is far from its own normal: more than 2.5 standard deviations from the previous 60 trading days. So 4% is a lot for Itaú and little for Magazine Luiza. Comparing with the Ibovespa (the main Brazilian index) on the same day separates stock-specific moves from market-wide ones.",
      m2h: "How the AI explains",
      m2p: (model) => `For each day we fetch up to 10 Google News headlines, from the previous trading day to the day after. The ${model} model reads only those headlines and cites the ones it used. When they do not explain the move, the answer is “no clear explanation” rather than a guess.`,
      m3h: "How we check it",
      m3p: "The model cites sources by the number each headline has in the list, and the code turns numbers into links. So no source can be invented.",
      m3pHuman: (n, who) => `The model cites sources by the number each headline has in the list, and the code turns numbers into links, so no source can be invented. We also drew ${n} days and judged each explanation as right, partly right or wrong. Judged by: ${who}. The most common error is offering a weak, low-confidence reason instead of saying the news does not explain the move.`,
      labeler: (l) => `${l.model} as a judge (LLM-as-judge); human review ${l.human_reviewed ? "done" : "pending"}`,
      limits: "Limits: the AI reads headlines only, not the articles. Google News returns slightly different results on each search. The checked sample is small. Nothing here is investment advice.",
      footer: (d) => `Adjusted prices from Yahoo Finance and headlines from Google News, updated every business day after the close. Last update: ${d}. `,
      code: "Code on GitHub",
    },
  };
  const qLang = new URLSearchParams(location.search).get("lang");
  let lang = document.documentElement.lang === "en" ? "en" : "pt"; // chosen in <head> before paint
  let L = STR[lang];

  // ---------- formatting (per language) ----------
  const $ = (s) => document.querySelector(s);
  const num = (x, d) => x.toLocaleString(LOCALE[lang], { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (x, d = 1) => `${x >= 0 ? "+" : "−"}${num(Math.abs(x * 100), d)}%`;
  const brl = (x) => `R$ ${num(x, 2)}`;
  const usd = (x, d) => `US$ ${num(x, d)}`;
  const share = (x) => `${num(x, 1)}%`;
  const parts = (iso) => [+iso.slice(8, 10), L.months[+iso.slice(5, 7) - 1], iso.slice(0, 4)];
  const dayYear = (iso) => L.dayYear(...parts(iso));
  const typeOf = (ev) => L.types[ev.ai.type] || L.types.unknown;
  const COLORS = { macro: "--macro", sector: "--sector", company: "--company", unknown: "--unknown" };
  const colorOf = (ev) => COLORS[ev.ai.type] || COLORS.unknown;
  // AI text in the current language; events from before the EN fields existed fall back to Portuguese.
  const reason = (ev) => (lang === "en" && ev.ai.short_reason_en) || ev.ai.short_reason;
  const explanation = (ev) => (lang === "en" && ev.ai.explanation_en) || ev.ai.explanation;

  function el(tag, props = {}, kids = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === "text") n.textContent = v;
      else if (k === "style") n.style.cssText = v;
      else n.setAttribute(k, v);
    }
    for (const c of [].concat(kids)) if (c != null) n.append(c);
    return n;
  }
  const safeUrl = (u) => (/^https?:\/\//i.test(u) ? u : "#");

  // Canvas cannot read light-dark() variables: resolve them through a probe element.
  const probe = document.body.appendChild(el("span", { style: "display:none" }));
  const color = (v) => { probe.style.color = `var(${v})`; return getComputedStyle(probe).color; };

  async function getJSON(path) {
    const r = await fetch(path, { cache: "no-cache" });
    if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
    return r.json();
  }

  const state = { index: null, ibov: [], ticker: null, prices: [], events: [], sel: null, summary: null };
  const cache = {};
  let chart, series;

  // ---------- chart ----------
  function theme() {
    return {
      layout: { background: { type: ColorType.Solid, color: color("--bg") }, textColor: color("--ink-2"), fontFamily: "Literata, Georgia, serif", fontSize: 13, attributionLogo: true },
      grid: { vertLines: { visible: false }, horzLines: { color: color("--rule") } },
      rightPriceScale: { borderVisible: false },
      timeScale: {
        borderVisible: false,
        tickMarkFormatter: (t, type) => {
          const [y, m, d] = (typeof t === "string" ? t : `${t.year}-${t.month}-${t.day}`).split("-").map(Number);
          return type === 0 ? String(y) : type === 1 ? L.months[m - 1] : L.dayMonth(d, L.months[m - 1]); // 2 = day (the 1st was not a trading day)
        },
      },
      crosshair: { mode: CrosshairMode.Magnet },
      localization: { locale: LOCALE[lang], priceFormatter: (x) => num(x, 2) },
    };
  }

  function buildChart() {
    chart = createChart($("#chart"), { autoSize: true, ...theme() });
    series = chart.addSeries(LineSeries, { color: color("--line"), lineWidth: 2, priceLineVisible: false, lastValueVisible: true });
    chart.subscribeClick((p) => {
      const ev = state.events.find((e) => e.date === (p.hoveredObjectId || p.time));
      if (ev) select(ev);
    });
    chart.subscribeCrosshairMove(tooltip);
    // Pins and callout are HTML over the canvas, so they must follow the chart's own
    // geometry. Wait two frames: the chart redraws (and rescales) on its own frame,
    // and reading coordinates before that returned stale positions on phones.
    const relayout = () => requestAnimationFrame(() => requestAnimationFrame(() => { placePins(); placeCallout(); }));
    chart.timeScale().subscribeVisibleLogicalRangeChange(relayout);
    chart.timeScale().subscribeSizeChange(relayout); // the canvas resized (autoSize)
    new ResizeObserver(relayout).observe($(".chart-box"));
    state.relayout = relayout;
  }

  // Pins are HTML buttons over the canvas: readable letters, a 40px tap area and keyboard focus.
  // Up moves sit below the line pointing up; down moves sit above it pointing down.
  function paintMarkers() {
    $("#pins").replaceChildren(...state.events.map((ev) => {
      const t = typeOf(ev), up = ev.return >= 0;
      const b = el("button", { type: "button", class: `pin ${up ? "up" : "down"}${state.sel === ev ? " sel" : ""}`, style: `--c:var(${colorOf(ev)})`,
        "aria-label": `${dayYear(ev.date)}, ${pct(ev.return)}, ${t.name}`, text: t.letter });
      b.dataset.d = ev.date;
      b.addEventListener("click", () => select(ev));
      return b;
    }));
    placePins();
  }

  function placePins() {
    if (!chart) return;
    const W = chart.timeScale().width();
    for (const b of $("#pins").children) {
      const ev = state.events.find((e) => e.date === b.dataset.d);
      const bar = state.prices.find((p) => p.time === ev.date);
      const x = chart.timeScale().timeToCoordinate(ev.date);
      const y = bar ? series.priceToCoordinate(bar.close) : null;
      const show = x != null && y != null && x >= 0 && x <= W;
      b.hidden = !show;
      if (show) { b.style.left = `${x}px`; b.style.top = `${y + (ev.return >= 0 ? 20 : -20)}px`; }
    }
  }

  // The selected day gets a label with a leader line, placed where the line is not.
  function placeCallout() {
    const box = $("#callout"), ev = state.sel;
    if (!ev || !chart) { box.hidden = true; return; }
    const x = chart.timeScale().timeToCoordinate(ev.date);
    const bar = state.prices.find((p) => p.time === ev.date);
    const y = bar ? series.priceToCoordinate(bar.close) : null;
    if (x == null || y == null) { box.hidden = true; return; }
    box.hidden = false;
    const label = box.querySelector(".callout-box"), leader = box.querySelector(".leader");
    label.replaceChildren(el("b", { text: ev.ai.type === "unknown" ? L.unknownShort : reason(ev) }), el("span", { text: `${dayYear(ev.date)}, ${pct(ev.return)}` }));
    const W = chart.timeScale().width(), H = $(".chart-box").clientHeight - chart.timeScale().height();
    const w = label.offsetWidth, h = label.offsetHeight, gap = 22;
    const left = Math.min(Math.max(0, x - w / 2), Math.max(0, W - w));
    const top = y > h + gap + 34 ? 4 : H - h - 4; // above the point and its pin if there is room, else at the bottom
    label.style.left = `${left}px`; label.style.top = `${top}px`;
    const a = top < y ? top + h : y + 34, b = top < y ? y - 34 : top; // the leader stops at the pin
    leader.style.left = `${x}px`; leader.style.top = `${a}px`; leader.style.height = `${Math.max(0, b - a)}px`;
  }

  function tooltip(p) {
    const tip = $("#tooltip");
    const bar = p.point && p.time ? p.seriesData.get(series) : null;
    if (!bar) { tip.hidden = true; return; }
    const ev = state.events.find((e) => e.date === p.time);
    tip.replaceChildren(
      el("div", { text: `${dayYear(p.time)}: ${brl(bar.value)}` }),
      ev ? el("div", { text: L.tipDay(pct(ev.return), ev.ai.type === "unknown" ? `${L.unknownShort}.` : reason(ev)) }) : null,
    );
    tip.hidden = false;
    const W = $(".chart-box").clientWidth, w = tip.offsetWidth;
    tip.style.left = `${Math.min(p.point.x + 14, W - w - 4)}px`;
    tip.style.top = `${Math.max(4, p.point.y - tip.offsetHeight - 14)}px`;
  }

  // ---------- text panels ----------
  function finding() {
    const counts = {};
    for (const e of state.events) if (e.ai.type !== "unknown") counts[e.ai.type] = (counts[e.ai.type] || 0) + 1;
    const best = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return L.finding(state.ticker, state.events.length, best ? { count: best[1], many: L.types[best[0]].many } : null);
  }

  function figures() {
    const p = state.prices, first = p[0], last = p.at(-1);
    const ib = state.ibov.filter((b) => b.time >= first.time);
    const evs = state.events;
    const up = evs.length ? evs.reduce((a, b) => (b.return > a.return ? b : a)) : null;
    const down = evs.length ? evs.reduce((a, b) => (b.return < a.return ? b : a)) : null;
    const items = [
      [L.fig.close, brl(last.close), dayYear(last.time)],
      [L.fig.change, pct(last.close / first.close - 1), ib.length ? `Ibovespa ${pct(ib.at(-1).close / ib[0].close - 1)}` : ""],
      [L.fig.up, up && up.return > 0 ? pct(up.return) : "—", up && up.return > 0 ? dayYear(up.date) : ""],
      [L.fig.down, down && down.return < 0 ? pct(down.return) : "—", down && down.return < 0 ? dayYear(down.date) : ""],
    ];
    $("#figures").replaceChildren(...items.map(([k, v, s]) => el("div", {}, [el("dt", { text: k }), el("dd", {}, [v, s ? el("small", { text: s }) : null])])));
  }

  function detail() {
    const box = $("#detail"), ev = state.sel;
    if (!ev) { box.replaceChildren(el("p", { class: "fine", text: L.noEvents })); return; }
    const t = typeOf(ev), i = state.events.indexOf(ev);
    // Headlines stay in Portuguese: they are the original sources the model read.
    const sources = ev.ai.sources.length
      ? el("ol", { class: "sources", lang: "pt-BR" }, ev.ai.sources.map((s) => el("li", {}, [
          el("a", { href: safeUrl(s.url), target: "_blank", rel: "noopener noreferrer", text: s.title }), " ", el("span", { class: "src", text: s.source })])))
      : el("p", { class: "fine", text: L.noSources });
    const step = (label, target) => {
      const b = el("button", { class: "step", type: "button", text: label });
      if (!target) b.disabled = true; else b.addEventListener("click", () => select(target, true));
      return b;
    };
    box.replaceChildren(
      el("p", { class: "when", text: L.when(dayYear(ev.date), i + 1, state.events.length) }),
      el("div", { class: "move" }, [el("b", { text: pct(ev.return, 2) }), el("span", { text: L.ibovSame(pct(ev.ibov_return, 2)) })]),
      el("h3", { text: ev.ai.type === "unknown" ? L.unknownTitle : reason(ev) }),
      el("p", { class: "kind" }, [el("i", { class: "sw", style: `background:var(${colorOf(ev)})` }), L.kind(t.name, L.conf[ev.ai.confidence] || "?")]),
      el("p", { class: "text", text: explanation(ev) }),
      el("h3", { text: L.sourcesTitle(ev.ai.sources.length, ev.news.length), style: "font-size:16px" }),
      sources,
      el("p", { class: "fine", text: L.aiNote(ev.ai.meta.model) }),
      el("div", { class: "steps" }, [step(L.prev, state.events[i - 1]), step(L.next, state.events[i + 1])]),
    );
  }

  function table() {
    $("#events-head").replaceChildren(...L.head.map((h, i) => el("th", { class: i === 1 || i === 2 ? "r" : "", text: h })));
    const rows = [...state.events].reverse().map((ev) => {
      const t = typeOf(ev);
      const tr = el("tr", { tabindex: "0", "aria-selected": String(state.sel === ev) }, [
        el("td", { class: "nw num", "data-l": L.head[0], text: dayYear(ev.date) }),
        el("td", { class: "r nw", "data-l": L.head[1], text: pct(ev.return) }),
        el("td", { class: "r nw", "data-l": L.head[2], text: pct(ev.ibov_return) }),
        el("td", { class: "nw", "data-l": L.head[3] }, [el("span", {}, [el("i", { class: "sw", style: `background:var(${colorOf(ev)});margin-right:6px` }), t.name])]),
        el("td", { class: "reason", "data-l": L.head[4], text: ev.ai.type === "unknown" ? "—" : reason(ev) }),
        el("td", { class: "nw", "data-l": L.head[5], text: L.conf[ev.ai.confidence] || "?" }),
      ]);
      tr.addEventListener("click", () => select(ev, true));
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(ev, true); } });
      return tr;
    });
    $("#events tbody").replaceChildren(...rows);
    $("#events-title").textContent = L.eventsTitle(state.ticker);
  }

  function legend() {
    const keys = ["company", "sector", "macro", "unknown"].map((k) =>
      el("span", {}, [el("i", { class: "key", style: `--c:var(${COLORS[k]})`, text: L.types[k].letter }), L.types[k].name]));
    $("#legend").replaceChildren(...keys, el("span", { class: "quiet", text: L.legendHint }));
  }

  function method() {
    const s = state.summary;
    $("#m3p").textContent = L.m3p;
    if (!s) { $("#eval-title").textContent = L.evalTitleDefault; $("#m2p").textContent = L.m2p("Claude"); return; }
    const a = s.automatic, h = s.human, c = s.cost, T = L.tiles;
    $("#eval-title").textContent = h ? L.evalTitle(h.labeled, share(h.accuracy_pct), share(h.accuracy_by_confidence.high)) : L.evalTitleDefault;
    const items = [
      [T.grounded[0], share(a.sources_grounded_pct), T.grounded[1](a.sources_cited)],
      [T.acc[0], h ? share(h.accuracy_pct) : "—", h ? T.acc[1](share(h.strict_accuracy_pct)) : T.acc[2]],
      [T.explained[0], T.explained[1](a.explained, a.events), T.explained[2](a.no_clear_explanation)],
      [T.cost[0], usd(c.cost_per_event_usd, 4), T.cost[1](usd(c.total_cost_usd, 2))],
    ];
    $("#eval-figures").replaceChildren(...items.map(([k, v, sub]) => el("div", {}, [el("dt", { text: k }), el("dd", {}, [v, el("small", { text: sub })])])));
    $("#m2p").textContent = L.m2p(s.model);
    if (h) $("#m3p").textContent = L.m3pHuman(h.labeled, L.labeler(h.labeler));
  }

  function footer() {
    const d = new Date(state.index.updated_at).toLocaleString(LOCALE[lang], { dateStyle: "short", timeStyle: "short" });
    $("#footer").replaceChildren(L.footer(d), el("a", { href: "https://github.com/beapama/b3-explained-chart", text: L.code }), ".");
  }

  // Everything that has text, in one place: called on load and on every language switch.
  function renderText() {
    document.documentElement.lang = lang === "en" ? "en" : "pt-BR";
    document.title = L.brand;
    document.querySelector('meta[name="description"]').setAttribute("content", L.metaDesc);
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = L[n.dataset.i18n]; });
    document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    $("#tickers").setAttribute("aria-label", L.tickersLabel);
    $("#chart").setAttribute("aria-label", L.chartAria);
    legend(); method();
    if (state.index) footer();
    if (state.ticker) {
      $("#finding").textContent = finding();
      figures(); paintMarkers(); detail(); table(); placeCallout();
      chart.applyOptions(theme()); // month names and number format on the axes
      state.relayout();
    }
  }

  function setLang(next) {
    if (next === lang) return;
    lang = next; L = STR[lang];
    localStorage.setItem("lang", lang);
    const url = new URL(location.href);
    url.searchParams.set("lang", lang); // shareable: the URL always says which language you see
    history.replaceState(null, "", url);
    renderText();
  }

  function select(ev, focus = false) {
    state.sel = ev;
    for (const b of $("#pins").children) b.classList.toggle("sel", b.dataset.d === ev?.date);
    detail(); table(); placeCallout(); state.relayout();
    if (focus && ev) {
      const d = new Date(ev.date), from = new Date(d), to = new Date(d);
      from.setDate(d.getDate() - 60); to.setDate(d.getDate() + 60);
      chart.timeScale().setVisibleRange({ from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) });
      $(".plate").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  }

  async function load(ticker) {
    state.ticker = ticker;
    const url = new URL(location.href); url.hash = ticker; // keep ?lang= when switching ticker
    history.replaceState(null, "", url);
    document.querySelectorAll("#tickers button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.t === ticker)));
    if (!cache[ticker]) {
      const [prices, events] = await Promise.all([getJSON(`data/prices/${ticker}.json`), getJSON(`data/events/${ticker}.json`).catch(() => [])]);
      cache[ticker] = { prices, events };
    }
    // Last 12 months only; the extra warm-up history exists for the detector.
    const c = new Date(); c.setFullYear(c.getFullYear() - 1);
    const from = c.toISOString().slice(0, 10);
    state.prices = cache[ticker].prices.filter((p) => p.time >= from);
    state.events = cache[ticker].events.filter((e) => e.date >= from);
    state.sel = state.events.at(-1) || null;
    $("#finding").textContent = finding();
    figures();
    series.setData(state.prices.map((p) => ({ time: p.time, value: p.close })));
    chart.timeScale().fitContent();
    paintMarkers();
    select(state.sel);
    state.relayout(); // new data rescales the chart: re-place pins once it has redrawn
  }

  async function main() {
    if (qLang && STR[qLang]) localStorage.setItem("lang", qLang); // a shared link sets the language
    document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));
    renderText();
    try { state.index = await getJSON("data/index.json"); }
    catch (err) { $("#finding").textContent = L.loadError; throw err; }
    footer();
    $("#tickers").replaceChildren(...state.index.tickers.map(({ ticker, name }) => {
      const b = el("button", { type: "button", "data-t": ticker, "aria-pressed": "false", title: name, text: ticker });
      b.addEventListener("click", () => load(ticker));
      return b;
    }));
    buildChart();
    state.ibov = await getJSON(`data/prices/${state.index.index}.json`).catch(() => []);
    const h = location.hash.slice(1);
    await load(state.index.tickers.some((t) => t.ticker === h) ? h : state.index.tickers[0].ticker);
    getJSON("data/eval_summary.json").then((s) => { state.summary = s; method(); }).catch(() => {});
    // Follow the system theme: recolour the canvas when it changes.
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      chart.applyOptions(theme()); series.applyOptions({ color: color("--line") });
    });
  }

  main();
}
