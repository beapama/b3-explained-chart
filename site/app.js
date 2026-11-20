// Pregão Explicado: reads the static JSON written by the Python pipeline.
// No framework, no build step. News text is untrusted, so the DOM is built
// with textContent only (no innerHTML with data).
{
  const { createChart, LineSeries, ColorType, CrosshairMode } = LightweightCharts;

  const TYPES = {
    macro:   { letter: "M", name: "Mercado inteiro", many: "acompanharam o mercado inteiro", color: "--macro" },
    sector:  { letter: "S", name: "Setor", many: "vieram de notícias do setor", color: "--sector" },
    company: { letter: "E", name: "Empresa", many: "vieram de notícias da própria empresa", color: "--company" },
    unknown: { letter: "?", name: "Sem explicação clara", many: "", color: "--unknown" },
  };
  const CONF = { high: "alta", medium: "média", low: "baixa" };
  const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

  const $ = (s) => document.querySelector(s);
  const pct = (x, d = 1) => `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(d).replace(".", ",")}%`;
  const brl = (x) => x.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const day = (iso) => `${+iso.slice(8, 10)} ${MONTHS[+iso.slice(5, 7) - 1]}`;
  const dayYear = (iso) => `${day(iso)} ${iso.slice(0, 4)}`;
  const typeOf = (ev) => TYPES[ev.ai.type] || TYPES.unknown;

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

  const state = { index: null, ibov: [], ticker: null, prices: [], events: [], sel: null };
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
          return type === 0 ? String(y) : type === 1 ? MONTHS[m - 1] : `${d} ${MONTHS[m - 1]}`; // 2 = day (1st was not a trading day)
        },
      },
      crosshair: { mode: CrosshairMode.Magnet },
    };
  }

  function buildChart() {
    chart = createChart($("#chart"), { autoSize: true, ...theme(), localization: { locale: "pt-BR", priceFormatter: brl } });
    series = chart.addSeries(LineSeries, { color: color("--line"), lineWidth: 2, priceLineVisible: false, lastValueVisible: true });
    chart.subscribeClick((p) => {
      const ev = state.events.find((e) => e.date === (p.hoveredObjectId || p.time));
      if (ev) select(ev);
    });
    chart.subscribeCrosshairMove(tooltip);
    const relayout = () => requestAnimationFrame(() => { placePins(); placeCallout(); });
    chart.timeScale().subscribeVisibleLogicalRangeChange(relayout);
    new ResizeObserver(relayout).observe($(".chart-box"));
  }

  // Pins are HTML buttons over the canvas: readable letters, a 40px tap area and keyboard focus.
  // Up moves sit below the line pointing up; down moves sit above it pointing down.
  function paintMarkers() {
    $("#pins").replaceChildren(...state.events.map((ev) => {
      const t = typeOf(ev), up = ev.return >= 0;
      const b = el("button", { type: "button", class: `pin ${up ? "up" : "down"}`, style: `--c:var(${t.color})`,
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
    label.replaceChildren(el("b", { text: ev.ai.type === "unknown" ? "Sem explicação clara" : ev.ai.short_reason }), el("span", { text: `${dayYear(ev.date)}, ${pct(ev.return)}` }));
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
      el("div", { text: `${dayYear(p.time)}: R$ ${brl(bar.value)}` }),
      ev ? el("div", { text: `${pct(ev.return)} no dia. ${ev.ai.type === "unknown" ? "Sem explicação clara." : ev.ai.short_reason}` }) : null,
    );
    tip.hidden = false;
    const W = $(".chart-box").clientWidth, w = tip.offsetWidth;
    tip.style.left = `${Math.min(p.point.x + 14, W - w - 4)}px`;
    tip.style.top = `${Math.max(4, p.point.y - tip.offsetHeight - 14)}px`;
  }

  // ---------- text panels ----------
  function finding() {
    const n = state.events.length, t = state.ticker;
    if (!n) return `${t} não teve dias de movimento forte nos últimos 12 meses.`;
    const counts = {};
    for (const e of state.events) if (e.ai.type !== "unknown") counts[e.ai.type] = (counts[e.ai.type] || 0) + 1;
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    const head = `${t} teve ${n} ${n === 1 ? "dia" : "dias"} de movimento forte em 12 meses`;
    return top ? `${head}; ${top[1]} ${TYPES[top[0]].many}.` : `${head}.`;
  }

  function figures() {
    const p = state.prices, first = p[0], last = p.at(-1);
    const ib = state.ibov.filter((b) => b.time >= first.time);
    const evs = state.events;
    const up = evs.length ? evs.reduce((a, b) => (b.return > a.return ? b : a)) : null;
    const down = evs.length ? evs.reduce((a, b) => (b.return < a.return ? b : a)) : null;
    const items = [
      ["Fechamento", `R$ ${brl(last.close)}`, dayYear(last.time)],
      ["Em 12 meses", pct(last.close / first.close - 1), ib.length ? `Ibovespa ${pct(ib.at(-1).close / ib[0].close - 1)}` : ""],
      ["Maior alta marcada", up && up.return > 0 ? pct(up.return) : "—", up && up.return > 0 ? dayYear(up.date) : ""],
      ["Maior queda marcada", down && down.return < 0 ? pct(down.return) : "—", down && down.return < 0 ? dayYear(down.date) : ""],
    ];
    $("#figures").replaceChildren(...items.map(([k, v, s]) => el("div", {}, [el("dt", { text: k }), el("dd", {}, [v, s ? el("small", { text: s }) : null])])));
  }

  function detail() {
    const box = $("#detail"), ev = state.sel;
    if (!ev) { box.replaceChildren(el("p", { class: "fine", text: "Nenhum dia marcado neste período." })); return; }
    const t = typeOf(ev), i = state.events.indexOf(ev);
    const sources = ev.ai.sources.length
      ? el("ol", { class: "sources" }, ev.ai.sources.map((s) => el("li", {}, [
          el("a", { href: safeUrl(s.url), target: "_blank", rel: "noopener noreferrer", text: s.title }), " ", el("span", { class: "src", text: s.source })])))
      : el("p", { class: "fine", text: "Nenhuma das manchetes encontradas explica o movimento." });
    const step = (label, target) => {
      const b = el("button", { class: "step", type: "button", text: label });
      if (!target) b.disabled = true; else b.addEventListener("click", () => select(target, true));
      return b;
    };
    box.replaceChildren(
      el("p", { class: "when", text: `${dayYear(ev.date)}, dia ${i + 1} de ${state.events.length}` }),
      el("div", { class: "move" }, [el("b", { text: pct(ev.return, 2) }), el("span", { text: `Ibovespa ${pct(ev.ibov_return, 2)} no mesmo dia` })]),
      el("h3", { text: ev.ai.type === "unknown" ? "As notícias não explicam este movimento" : ev.ai.short_reason }),
      el("p", { class: "kind" }, [el("i", { class: "sw", style: `background:var(${t.color})` }), `${t.name}, confiança ${CONF[ev.ai.confidence] || "?"}`]),
      el("p", { class: "text", text: ev.ai.explanation }),
      el("h3", { text: `Fontes citadas (${ev.ai.sources.length} de ${ev.news.length} manchetes lidas)`, style: "font-size:16px" }),
      sources,
      el("p", { class: "fine", text: `Texto escrito por IA (${ev.ai.meta.model}) a partir das manchetes acima. Pode conter erros.` }),
      el("div", { class: "steps" }, [step("← Anterior", state.events[i - 1]), step("Próximo →", state.events[i + 1])]),
    );
  }

  function table() {
    const rows = [...state.events].reverse().map((ev) => {
      const t = typeOf(ev);
      const tr = el("tr", { tabindex: "0", "aria-selected": String(state.sel === ev) }, [
        el("td", { class: "nw num", "data-l": "Data", text: dayYear(ev.date) }),
        el("td", { class: "r nw", "data-l": "Ação", text: pct(ev.return) }),
        el("td", { class: "r nw", "data-l": "Ibovespa", text: pct(ev.ibov_return) }),
        el("td", { class: "nw", "data-l": "Tipo" }, [el("span", {}, [el("i", { class: "sw", style: `background:var(${t.color});margin-right:6px` }), t.name])]),
        el("td", { class: "reason", "data-l": "Motivo", text: ev.ai.type === "unknown" ? "—" : ev.ai.short_reason }),
        el("td", { class: "nw", "data-l": "Confiança", text: CONF[ev.ai.confidence] || "?" }),
      ]);
      tr.addEventListener("click", () => select(ev, true));
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(ev, true); } });
      return tr;
    });
    $("#events tbody").replaceChildren(...rows);
    $("#events-title").textContent = `Todos os dias marcados de ${state.ticker}`;
  }

  function select(ev, focus = false) {
    state.sel = ev;
    for (const b of $("#pins").children) b.classList.toggle("sel", b.dataset.d === ev?.date);
    detail(); table(); placeCallout();
    if (focus && ev) {
      const d = new Date(ev.date), from = new Date(d), to = new Date(d);
      from.setDate(d.getDate() - 60); to.setDate(d.getDate() + 60);
      chart.timeScale().setVisibleRange({ from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) });
      $(".plate").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  }

  async function load(ticker) {
    state.ticker = ticker;
    history.replaceState(null, "", `#${ticker}`);
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
    $("#finding").textContent = finding();
    figures();
    series.setData(state.prices.map((p) => ({ time: p.time, value: p.close })));
    chart.timeScale().fitContent();
    paintMarkers();
    select(state.events.at(-1) || null);
  }

  function method(s) {
    const a = s.automatic, h = s.human, c = s.cost;
    const f = (x) => `${String(x).replace(".", ",")}%`;
    $("#eval-title").textContent = h
      ? `Em ${h.labeled} explicações conferidas, ${f(h.accuracy_pct)} estavam certas; com confiança alta, ${f(h.accuracy_by_confidence.high)}`
      : "Como a IA é conferida";
    const items = [
      ["Fontes conferidas", f(a.sources_grounded_pct), `${a.sources_cited} citações, nenhuma inventada`],
      ["Acertos na amostra", h ? f(h.accuracy_pct) : "—", h ? `${f(h.strict_accuracy_pct)} sem contar parciais` : "pendente"],
      ["Dias explicados", `${a.explained} de ${a.events}`, `${a.no_clear_explanation} sem explicação clara`],
      ["Custo por explicação", `US$ ${c.cost_per_event_usd.toFixed(4).replace(".", ",")}`, `US$ ${c.total_cost_usd.toFixed(2).replace(".", ",")} no total`],
    ];
    $("#eval-figures").replaceChildren(...items.map(([k, v, sub]) => el("div", {}, [el("dt", { text: k }), el("dd", {}, [v, el("small", { text: sub })])])));
    $("#eval-model").textContent = s.model;
    if (h) $("#eval-check").textContent = `O modelo cita as fontes pelo número que cada manchete tem na lista, e o código troca o número pelo link, então nenhuma fonte pode ser inventada. Também sorteamos ${h.labeled} dias e julgamos cada explicação como certa, parcial ou errada. Quem julgou: ${h.labeler}. O erro mais comum é arriscar um motivo fraco, com confiança baixa, em vez de dizer que as notícias não explicam.`;
  }

  async function main() {
    try { state.index = await getJSON("data/index.json"); }
    catch (err) { $("#finding").textContent = "Não foi possível carregar os dados."; throw err; }
    $("#updated-at").textContent = new Date(state.index.updated_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
    $("#tickers").replaceChildren(...state.index.tickers.map(({ ticker, name }) => {
      const b = el("button", { type: "button", "data-t": ticker, "aria-pressed": "false", title: name, text: ticker });
      b.addEventListener("click", () => load(ticker));
      return b;
    }));
    buildChart();
    state.ibov = await getJSON(`data/prices/${state.index.index}.json`).catch(() => []);
    const h = location.hash.slice(1);
    await load(state.index.tickers.some((t) => t.ticker === h) ? h : state.index.tickers[0].ticker);
    getJSON("data/eval_summary.json").then(method).catch(() => {});
    // Follow the system theme: recolour the canvas when it changes.
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      chart.applyOptions(theme()); series.applyOptions({ color: color("--line") });
    });
  }

  main();
}
