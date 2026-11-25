/**
 * B3 Moves, Explained: renders the static JSON written by the Python pipeline.
 *
 * No framework and no build step. Every text the user sees comes from STRINGS,
 * so the PT | EN switch reaches all of it. News text is untrusted, so the DOM
 * is built with textContent only.
 */
{
  const { createChart, LineSeries, ColorType, CrosshairMode, TickMarkType } = LightweightCharts;

  const REPO_URL = "https://github.com/beapama/b3-explained-chart";
  const LOCALES = { pt: "pt-BR", en: "en-US" };
  const HTML_LANG = { pt: "pt-BR", en: "en" };
  const TYPE_COLORS = { macro: "--macro", sector: "--sector", company: "--company", unknown: "--unknown" };
  const LEGEND_ORDER = ["company", "sector", "macro", "unknown"];

  const PIN_OFFSET_PX = 20;
  const PIN_REACH_PX = 34;
  const CALLOUT_GAP_PX = 22;
  const EDGE_MARGIN_PX = 4;
  const TOOLTIP_OFFSET_PX = 14;
  const FOCUS_WINDOW_DAYS = 60;

  const STRINGS = {
    pt: {
      brand: "B3 Moves, Explained",
      tagline: "Os dias de movimento forte de cinco ações da B3, com o motivo de cada um segundo as notícias.",
      metaDesc: "Os dias de movimento forte de cinco ações da B3 nos últimos 12 meses, com o motivo de cada um segundo as notícias.",
      tickersLabel: "Escolha a ação",
      loading: "Carregando…",
      loadError: "Não foi possível carregar os dados.",
      months: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
      dayMonth: (day, month) => `${day} ${month}`,
      dayYear: (day, month, year) => `${day} ${month} ${year}`,
      types: {
        macro: { letter: "M", name: "Mercado inteiro", many: "acompanharam o mercado inteiro" },
        sector: { letter: "S", name: "Setor", many: "vieram de notícias do setor" },
        company: { letter: "E", name: "Empresa", many: "vieram de notícias da própria empresa" },
        unknown: { letter: "?", name: "Sem explicação clara", many: "" },
      },
      conf: { high: "alta", medium: "média", low: "baixa" },
      legendHint: "A ponta do marcador indica alta (para cima) ou queda (para baixo). Clique num marcador para ler o motivo.",
      chartAria: "Preço de fechamento nos últimos 12 meses com os dias de movimento forte marcados",
      finding: (ticker, count, top) => {
        if (!count) return `${ticker} não teve dias de movimento forte nos últimos 12 meses.`;
        const head = `${ticker} teve ${count} ${count === 1 ? "dia" : "dias"} de movimento forte em 12 meses`;
        return top ? `${head}; ${top.count} ${top.many}.` : `${head}.`;
      },
      fig: { close: "Fechamento", change: "Em 12 meses", up: "Maior alta marcada", down: "Maior queda marcada" },
      noEvents: "Nenhum dia marcado neste período.",
      when: (date, position, total) => `${date}, dia ${position} de ${total}`,
      ibovSame: (change) => `Ibovespa ${change} no mesmo dia`,
      unknownTitle: "As notícias não explicam este movimento",
      unknownShort: "Sem explicação clara",
      kind: (name, conf) => `${name}, confiança ${conf}`,
      sourcesTitle: (cited, read) => `Fontes citadas (${cited} de ${read} manchetes lidas)`,
      noSources: "Nenhuma das manchetes encontradas explica o movimento.",
      aiNote: (model) => `Texto escrito por IA (${model}) a partir das manchetes acima. Pode conter erros.`,
      prev: "← Anterior",
      next: "Próximo →",
      tipDay: (change, why) => `${change} no dia. ${why}`,
      eventsTitle: (ticker) => `Todos os dias marcados de ${ticker}`,
      head: ["Data", "Ação", "Ibovespa", "Tipo", "Motivo", "Confiança"],
      evalTitle: (n, acc, high) => `Em ${n} explicações conferidas, ${acc} estavam certas; com confiança alta, ${high}`,
      evalTitleDefault: "Como a IA é conferida",
      tiles: {
        grounded: ["Fontes conferidas", (n) => `${n} citações, nenhuma inventada`],
        acc: ["Acertos na amostra", (strict) => `${strict} sem contar parciais`, "pendente"],
        explained: ["Dias explicados", (done, all) => `${done} de ${all}`, (n) => `${n} sem explicação clara`],
        cost: ["Custo por explicação", (total) => `${total} no total`],
      },
      m1h: "Como os dias são escolhidos",
      m1p: "Um dia entra no gráfico quando a variação da ação foge muito do normal dela: mais de 2,5 desvios-padrão em relação aos 60 pregões anteriores. Assim, 4% é muito para o Itaú e pouco para a Magazine Luiza. A comparação com o Ibovespa no mesmo dia separa o que foi da ação do que foi do mercado.",
      m2h: "Como a IA explica",
      m2p: (model) => `Para cada dia buscamos até 10 manchetes no Google News, do pregão anterior ao dia seguinte. O modelo ${model} lê só essas manchetes e cita as que usou. Quando elas não explicam o movimento, a resposta é “sem explicação clara”, e não um palpite.`,
      m3h: "Como conferimos",
      m3p: "O modelo cita as fontes pelo número que cada manchete tem na lista, e o código troca o número pelo link. Por isso nenhuma fonte pode ser inventada.",
      m3pHuman: (n, who) => `O modelo cita as fontes pelo número que cada manchete tem na lista, e o código troca o número pelo link, então nenhuma fonte pode ser inventada. Também sorteamos ${n} dias e julgamos cada explicação como certa, parcial ou errada. Quem julgou: ${who}. O erro mais comum é arriscar um motivo fraco, com confiança baixa, em vez de dizer que as notícias não explicam.`,
      labeler: (labeler) => `${labeler.model} como juiz (LLM-as-judge); revisão humana ${labeler.human_reviewed ? "feita" : "pendente"}`,
      limits: "Limites: a IA lê só manchetes, não o texto das matérias. O Google News devolve resultados um pouco diferentes a cada busca. A amostra conferida é pequena. Nada aqui é recomendação de investimento.",
      footer: (updated) => `Preços ajustados do Yahoo Finance e manchetes do Google News, atualizados todo dia útil depois do fechamento. Última atualização: ${updated}. `,
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
      dayMonth: (day, month) => `${month} ${day}`,
      dayYear: (day, month, year) => `${month} ${day}, ${year}`,
      types: {
        macro: { letter: "M", name: "Whole market", many: "followed the whole market" },
        sector: { letter: "S", name: "Sector", many: "came from sector news" },
        company: { letter: "C", name: "Company", many: "came from company news" },
        unknown: { letter: "?", name: "No clear explanation", many: "" },
      },
      conf: { high: "high", medium: "medium", low: "low" },
      legendHint: "The marker's tip points up for a rise and down for a fall. Click a marker to read why.",
      chartAria: "Closing price over the last 12 months with the days of strong moves marked",
      finding: (ticker, count, top) => {
        if (!count) return `${ticker} had no days of strong moves in the last 12 months.`;
        const head = `${ticker} had ${count} ${count === 1 ? "day" : "days"} of strong moves in 12 months`;
        return top ? `${head}; ${top.count} ${top.many}.` : `${head}.`;
      },
      fig: { close: "Close", change: "Last 12 months", up: "Biggest marked rise", down: "Biggest marked fall" },
      noEvents: "No days marked in this period.",
      when: (date, position, total) => `${date}, day ${position} of ${total}`,
      ibovSame: (change) => `Ibovespa ${change} the same day`,
      unknownTitle: "The news does not explain this move",
      unknownShort: "No clear explanation",
      kind: (name, conf) => `${name}, ${conf} confidence`,
      sourcesTitle: (cited, read) => `Sources cited (${cited} of ${read} headlines read, in Portuguese)`,
      noSources: "None of the headlines found explains the move.",
      aiNote: (model) => `Written by AI (${model}) from the headlines above, then translated to English. It may contain errors.`,
      prev: "← Previous",
      next: "Next →",
      tipDay: (change, why) => `${change} that day. ${why}`,
      eventsTitle: (ticker) => `Every marked day for ${ticker}`,
      head: ["Date", "Stock", "Ibovespa", "Type", "Reason", "Confidence"],
      evalTitle: (n, acc, high) => `Of ${n} explanations checked, ${acc} were right; ${high} when the model was confident`,
      evalTitleDefault: "How the AI is checked",
      tiles: {
        grounded: ["Sources verified", (n) => `${n} citations, none invented`],
        acc: ["Right in the sample", (strict) => `${strict} not counting partials`, "pending"],
        explained: ["Days explained", (done, all) => `${done} of ${all}`, (n) => `${n} with no clear explanation`],
        cost: ["Cost per explanation", (total) => `${total} in total`],
      },
      m1h: "How the days are picked",
      m1p: "A day is marked when the stock's return is far from its own normal: more than 2.5 standard deviations from the previous 60 trading days. So 4% is a lot for Itaú and little for Magazine Luiza. Comparing with the Ibovespa (the main Brazilian index) on the same day separates stock-specific moves from market-wide ones.",
      m2h: "How the AI explains",
      m2p: (model) => `For each day we fetch up to 10 Google News headlines, from the previous trading day to the day after. The ${model} model reads only those headlines and cites the ones it used. When they do not explain the move, the answer is “no clear explanation” rather than a guess.`,
      m3h: "How we check it",
      m3p: "The model cites sources by the number each headline has in the list, and the code turns numbers into links. So no source can be invented.",
      m3pHuman: (n, who) => `The model cites sources by the number each headline has in the list, and the code turns numbers into links, so no source can be invented. We also drew ${n} days and judged each explanation as right, partly right or wrong. Judged by: ${who}. The most common error is offering a weak, low-confidence reason instead of saying the news does not explain the move.`,
      labeler: (labeler) => `${labeler.model} as a judge (LLM-as-judge); human review ${labeler.human_reviewed ? "done" : "pending"}`,
      limits: "Limits: the AI reads headlines only, not the articles. Google News returns slightly different results on each search. The checked sample is small. Nothing here is investment advice.",
      footer: (updated) => `Adjusted prices from Yahoo Finance and headlines from Google News, updated every business day after the close. Last update: ${updated}. `,
      code: "Code on GitHub",
    },
  };

  const langFromUrl = new URLSearchParams(location.search).get("lang");
  let lang = document.documentElement.lang === "en" ? "en" : "pt";
  let ui = STRINGS[lang];

  const state = { index: null, ibov: [], ticker: null, prices: [], events: [], selected: null, summary: null };
  const tickerCache = {};
  let chart;
  let series;
  let relayout = () => {};

  const $ = (selector) => document.querySelector(selector);

  /** Formats a number in the current locale with exactly `digits` decimals. */
  const formatNumber = (value, digits) =>
    value.toLocaleString(LOCALES[lang], { minimumFractionDigits: digits, maximumFractionDigits: digits });

  /** Formats a return (0.0123) as a signed percentage (+1.2%), with a true minus sign. */
  const formatChange = (ratio, digits = 1) => `${ratio >= 0 ? "+" : "−"}${formatNumber(Math.abs(ratio * 100), digits)}%`;

  /** Formats a value that is already a percentage (98.5 → 98.5%). */
  const formatShare = (percent) => `${formatNumber(percent, 1)}%`;

  /** Formats Brazilian reais; the currency stays BRL in both languages. */
  const formatBrl = (value) => `R$ ${formatNumber(value, 2)}`;

  /** Formats US dollars, used for the API cost. */
  const formatUsd = (value, digits) => `US$ ${formatNumber(value, digits)}`;

  /** Formats an ISO date (2026-11-04) as "4 nov 2026" or "Nov 4, 2026". */
  const formatDate = (iso) => ui.dayYear(+iso.slice(8, 10), ui.months[+iso.slice(5, 7) - 1], iso.slice(0, 4));

  /** Returns the ISO date `days` days after (or before, if negative) the given date. */
  const shiftDate = (date, days) => {
    const shifted = new Date(date);
    shifted.setDate(shifted.getDate() + days);
    return shifted.toISOString().slice(0, 10);
  };

  const isUnexplained = (event) => event.ai.type === "unknown";
  const typeOf = (event) => ui.types[event.ai.type] || ui.types.unknown;
  const colorVarOf = (event) => TYPE_COLORS[event.ai.type] || TYPE_COLORS.unknown;
  const confidenceOf = (event) => ui.conf[event.ai.confidence] || "?";

  /** Returns the short reason in the current language, falling back to Portuguese for older events. */
  const reasonOf = (event) => (lang === "en" && event.ai.short_reason_en) || event.ai.short_reason;

  /** Returns the explanation in the current language, falling back to Portuguese for older events. */
  const explanationOf = (event) => (lang === "en" && event.ai.explanation_en) || event.ai.explanation;

  /** Returns the URL only if it is http(s), so a source can never inject a javascript: link. */
  const safeUrl = (url) => (/^https?:\/\//i.test(url) ? url : "#");

  /**
   * Creates a DOM element without ever parsing HTML.
   *
   * @param {string} tag element name
   * @param {Object} props attributes; `text` sets textContent and `style` sets inline CSS
   * @param {Node|string|Array} children appended in order; null entries are skipped
   */
  function el(tag, props = {}, children = []) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (key === "text") node.textContent = value;
      else if (key === "style") node.style.cssText = value;
      else node.setAttribute(key, value);
    }
    for (const child of [].concat(children)) if (child != null) node.append(child);
    return node;
  }

  const colorProbe = document.body.appendChild(el("span", { style: "display:none" }));

  /** Resolves a CSS variable to a concrete colour, since the canvas cannot read light-dark() values. */
  function cssColor(variable) {
    colorProbe.style.color = `var(${variable})`;
    return getComputedStyle(colorProbe).color;
  }

  /** Fetches a JSON file, bypassing stale HTTP caches, and fails on any non-2xx status. */
  async function getJSON(path) {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.json();
  }

  /** Returns the event on the given ISO date, if any. */
  const eventOn = (date) => state.events.find((event) => event.date === date);

  /** Returns the vertical pixel position of the closing price on the given date, or null when off the data. */
  function closeY(date) {
    const bar = state.prices.find((price) => price.time === date);
    return bar ? series.priceToCoordinate(bar.close) : null;
  }

  /** Formats an axis tick as a year, a month name or "day month", in the current language. */
  function formatTick(time, tickType) {
    const iso = typeof time === "string" ? time : `${time.year}-${time.month}-${time.day}`;
    const [year, month, day] = iso.split("-").map(Number);
    if (tickType === TickMarkType.Year) return String(year);
    if (tickType === TickMarkType.Month) return ui.months[month - 1];
    return ui.dayMonth(day, ui.months[month - 1]);
  }

  /** Returns chart options for the current theme and language. */
  function chartTheme() {
    return {
      layout: {
        background: { type: ColorType.Solid, color: cssColor("--bg") },
        textColor: cssColor("--ink-2"),
        fontFamily: "Literata, Georgia, serif",
        fontSize: 13,
        attributionLogo: true,
      },
      grid: { vertLines: { visible: false }, horzLines: { color: cssColor("--rule") } },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, tickMarkFormatter: formatTick },
      crosshair: { mode: CrosshairMode.Magnet },
      localization: { locale: LOCALES[lang], priceFormatter: (price) => formatNumber(price, 2) },
    };
  }

  /**
   * Creates the chart and keeps the HTML overlays (pins, callout) aligned with it.
   *
   * The overlays are re-placed two animation frames after any pan, zoom or resize:
   * the chart rescales on its own frame, and reading coordinates earlier returned
   * stale positions on phones.
   */
  function buildChart() {
    chart = createChart($("#chart"), { autoSize: true, ...chartTheme() });
    series = chart.addSeries(LineSeries, {
      color: cssColor("--line"),
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });
    chart.subscribeClick((param) => {
      const event = eventOn(param.hoveredObjectId || param.time);
      if (event) select(event);
    });
    chart.subscribeCrosshairMove(showTooltip);

    relayout = () =>
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          placePins();
          placeCallout();
        }),
      );
    chart.timeScale().subscribeVisibleLogicalRangeChange(relayout);
    chart.timeScale().subscribeSizeChange(relayout);
    new ResizeObserver(relayout).observe($(".chart-box"));
  }

  /**
   * Draws one HTML button per event over the chart.
   *
   * Buttons rather than canvas markers give readable letters, a large tap area
   * and keyboard focus. Rises sit below the line pointing up; falls sit above it
   * pointing down.
   */
  function paintPins() {
    const pins = state.events.map((event) => {
      const type = typeOf(event);
      const direction = event.return >= 0 ? "up" : "down";
      const pin = el("button", {
        type: "button",
        class: `pin ${direction}${state.selected === event ? " sel" : ""}`,
        style: `--c:var(${colorVarOf(event)})`,
        "aria-label": `${formatDate(event.date)}, ${formatChange(event.return)}, ${type.name}`,
        text: type.letter,
      });
      pin.dataset.d = event.date;
      pin.addEventListener("click", () => select(event));
      return pin;
    });
    $("#pins").replaceChildren(...pins);
    placePins();
  }

  /** Moves each pin to its day on the chart and hides the ones outside the visible range. */
  function placePins() {
    if (!chart) return;
    const width = chart.timeScale().width();
    for (const pin of $("#pins").children) {
      const event = eventOn(pin.dataset.d);
      const x = chart.timeScale().timeToCoordinate(event.date);
      const y = closeY(event.date);
      const visible = x != null && y != null && x >= 0 && x <= width;
      pin.hidden = !visible;
      if (visible) {
        pin.style.left = `${x}px`;
        pin.style.top = `${y + (event.return >= 0 ? PIN_OFFSET_PX : -PIN_OFFSET_PX)}px`;
      }
    }
  }

  /**
   * Labels the selected day with a callout joined to its pin by a leader line.
   *
   * The label goes at the top of the chart when there is room above the point
   * and its pin, otherwise at the bottom, so it never covers the line.
   */
  function placeCallout() {
    const callout = $("#callout");
    const event = state.selected;
    const x = event && chart ? chart.timeScale().timeToCoordinate(event.date) : null;
    const y = event && chart ? closeY(event.date) : null;
    if (x == null || y == null) {
      callout.hidden = true;
      return;
    }
    callout.hidden = false;

    const label = callout.querySelector(".callout-box");
    const leader = callout.querySelector(".leader");
    label.replaceChildren(
      el("b", { text: isUnexplained(event) ? ui.unknownShort : reasonOf(event) }),
      el("span", { text: `${formatDate(event.date)}, ${formatChange(event.return)}` }),
    );

    const plotWidth = chart.timeScale().width();
    const plotHeight = $(".chart-box").clientHeight - chart.timeScale().height();
    const labelWidth = label.offsetWidth;
    const labelHeight = label.offsetHeight;
    const left = Math.min(Math.max(0, x - labelWidth / 2), Math.max(0, plotWidth - labelWidth));
    const fitsAbove = y > labelHeight + CALLOUT_GAP_PX + PIN_REACH_PX;
    const top = fitsAbove ? EDGE_MARGIN_PX : plotHeight - labelHeight - EDGE_MARGIN_PX;
    label.style.left = `${left}px`;
    label.style.top = `${top}px`;

    const labelIsAbove = top < y;
    const leaderStart = labelIsAbove ? top + labelHeight : y + PIN_REACH_PX;
    const leaderEnd = labelIsAbove ? y - PIN_REACH_PX : top;
    leader.style.left = `${x}px`;
    leader.style.top = `${leaderStart}px`;
    leader.style.height = `${Math.max(0, leaderEnd - leaderStart)}px`;
  }

  /** Shows the price under the crosshair and, on an event day, its change and reason. */
  function showTooltip(param) {
    const tooltip = $("#tooltip");
    const bar = param.point && param.time ? param.seriesData.get(series) : null;
    if (!bar) {
      tooltip.hidden = true;
      return;
    }
    const event = eventOn(param.time);
    const why = event && (isUnexplained(event) ? `${ui.unknownShort}.` : reasonOf(event));
    tooltip.replaceChildren(
      el("div", { text: `${formatDate(param.time)}: ${formatBrl(bar.value)}` }),
      event ? el("div", { text: ui.tipDay(formatChange(event.return), why) }) : null,
    );
    tooltip.hidden = false;
    const boxWidth = $(".chart-box").clientWidth;
    tooltip.style.left = `${Math.min(param.point.x + TOOLTIP_OFFSET_PX, boxWidth - tooltip.offsetWidth - EDGE_MARGIN_PX)}px`;
    tooltip.style.top = `${Math.max(EDGE_MARGIN_PX, param.point.y - tooltip.offsetHeight - TOOLTIP_OFFSET_PX)}px`;
  }

  /** Returns the headline: how many strong days the ticker had and the most common explained type. */
  function findingText() {
    const counts = {};
    for (const event of state.events) {
      if (!isUnexplained(event)) counts[event.ai.type] = (counts[event.ai.type] || 0) + 1;
    }
    const [topType, topCount] = Object.entries(counts).sort((a, b) => b[1] - a[1])[0] || [];
    const top = topType ? { count: topCount, many: ui.types[topType].many } : null;
    return ui.finding(state.ticker, state.events.length, top);
  }

  /** Renders a <dl> of [label, value, note] figures into the given container. */
  function renderFigures(selector, items) {
    const cells = items.map(([label, value, note]) =>
      el("div", {}, [el("dt", { text: label }), el("dd", {}, [value, note ? el("small", { text: note }) : null])]),
    );
    $(selector).replaceChildren(...cells);
  }

  /** Renders the figures row: last close, 12-month change against the Ibovespa, biggest marked rise and fall. */
  function renderPriceFigures() {
    const first = state.prices[0];
    const last = state.prices.at(-1);
    const ibov = state.ibov.filter((bar) => bar.time >= first.time);
    const ibovChange = ibov.length ? `Ibovespa ${formatChange(ibov.at(-1).close / ibov[0].close - 1)}` : "";
    const biggestRise = state.events.filter((e) => e.return > 0).sort((a, b) => b.return - a.return)[0];
    const biggestFall = state.events.filter((e) => e.return < 0).sort((a, b) => a.return - b.return)[0];
    const extreme = (event) => (event ? [formatChange(event.return), formatDate(event.date)] : ["—", ""]);
    renderFigures("#figures", [
      [ui.fig.close, formatBrl(last.close), formatDate(last.time)],
      [ui.fig.change, formatChange(last.close / first.close - 1), ibovChange],
      [ui.fig.up, ...extreme(biggestRise)],
      [ui.fig.down, ...extreme(biggestFall)],
    ]);
  }

  /** Builds the list of cited headlines, kept in Portuguese because they are the original sources. */
  function sourceList(event) {
    if (!event.ai.sources.length) return el("p", { class: "fine", text: ui.noSources });
    const items = event.ai.sources.map((source) =>
      el("li", {}, [
        el("a", { href: safeUrl(source.url), target: "_blank", rel: "noopener noreferrer", text: source.title }),
        " ",
        el("span", { class: "src", text: source.source }),
      ]),
    );
    return el("ol", { class: "sources", lang: "pt-BR" }, items);
  }

  /** Builds a previous/next button, disabled when there is no event to go to. */
  function stepButton(label, target) {
    const button = el("button", { class: "step", type: "button", text: label });
    if (target) button.addEventListener("click", () => select(target, true));
    else button.disabled = true;
    return button;
  }

  /** Renders the notes column for the selected event. */
  function renderDetail() {
    const panel = $("#detail");
    const event = state.selected;
    if (!event) {
      panel.replaceChildren(el("p", { class: "fine", text: ui.noEvents }));
      return;
    }
    const position = state.events.indexOf(event);
    panel.replaceChildren(
      el("p", { class: "when", text: ui.when(formatDate(event.date), position + 1, state.events.length) }),
      el("div", { class: "move" }, [
        el("b", { text: formatChange(event.return, 2) }),
        el("span", { text: ui.ibovSame(formatChange(event.ibov_return, 2)) }),
      ]),
      el("h3", { text: isUnexplained(event) ? ui.unknownTitle : reasonOf(event) }),
      el("p", { class: "kind" }, [
        el("i", { class: "sw", style: `background:var(${colorVarOf(event)})` }),
        ui.kind(typeOf(event).name, confidenceOf(event)),
      ]),
      el("p", { class: "text", text: explanationOf(event) }),
      el("h3", { text: ui.sourcesTitle(event.ai.sources.length, event.news.length), style: "font-size:16px" }),
      sourceList(event),
      el("p", { class: "fine", text: ui.aiNote(event.ai.meta.model) }),
      el("div", { class: "steps" }, [
        stepButton(ui.prev, state.events[position - 1]),
        stepButton(ui.next, state.events[position + 1]),
      ]),
    );
  }

  /** Builds one table row; it is focusable and selects its event on click, Enter or Space. */
  function eventRow(event) {
    const [date, stock, ibov, type, reason, confidence] = ui.head;
    const row = el("tr", { tabindex: "0", "aria-selected": String(state.selected === event) }, [
      el("td", { class: "nw num", "data-l": date, text: formatDate(event.date) }),
      el("td", { class: "r nw", "data-l": stock, text: formatChange(event.return) }),
      el("td", { class: "r nw", "data-l": ibov, text: formatChange(event.ibov_return) }),
      el("td", { class: "nw", "data-l": type }, [
        el("span", {}, [
          el("i", { class: "sw", style: `background:var(${colorVarOf(event)});margin-right:6px` }),
          typeOf(event).name,
        ]),
      ]),
      el("td", { class: "reason", "data-l": reason, text: isUnexplained(event) ? "—" : reasonOf(event) }),
      el("td", { class: "nw", "data-l": confidence, text: confidenceOf(event) }),
    ]);
    row.addEventListener("click", () => select(event, true));
    row.addEventListener("keydown", (keyEvent) => {
      if (keyEvent.key === "Enter" || keyEvent.key === " ") {
        keyEvent.preventDefault();
        select(event, true);
      }
    });
    return row;
  }

  /** Renders the table of every marked day, newest first. */
  function renderTable() {
    const numericColumns = [1, 2];
    $("#events-head").replaceChildren(
      ...ui.head.map((title, i) => el("th", { class: numericColumns.includes(i) ? "r" : "", text: title })),
    );
    $("#events tbody").replaceChildren(...[...state.events].reverse().map(eventRow));
    $("#events-title").textContent = ui.eventsTitle(state.ticker);
  }

  /** Renders the colour key of event types under the chart. */
  function renderLegend() {
    const keys = LEGEND_ORDER.map((type) =>
      el("span", {}, [
        el("i", { class: "key", style: `--c:var(${TYPE_COLORS[type]})`, text: ui.types[type].letter }),
        ui.types[type].name,
      ]),
    );
    $("#legend").replaceChildren(...keys, el("span", { class: "quiet", text: ui.legendHint }));
  }

  /** Renders the "How the AI is checked" section from eval_summary.json, or its defaults before it loads. */
  function renderMethod() {
    const summary = state.summary;
    $("#m3p").textContent = ui.m3p;
    if (!summary) {
      $("#eval-title").textContent = ui.evalTitleDefault;
      $("#m2p").textContent = ui.m2p("Claude");
      return;
    }
    const { automatic, human, cost } = summary;
    const tiles = ui.tiles;
    $("#eval-title").textContent = human
      ? ui.evalTitle(human.labeled, formatShare(human.accuracy_pct), formatShare(human.accuracy_by_confidence.high))
      : ui.evalTitleDefault;
    renderFigures("#eval-figures", [
      [tiles.grounded[0], formatShare(automatic.sources_grounded_pct), tiles.grounded[1](automatic.sources_cited)],
      [
        tiles.acc[0],
        human ? formatShare(human.accuracy_pct) : "—",
        human ? tiles.acc[1](formatShare(human.strict_accuracy_pct)) : tiles.acc[2],
      ],
      [
        tiles.explained[0],
        tiles.explained[1](automatic.explained, automatic.events),
        tiles.explained[2](automatic.no_clear_explanation),
      ],
      [tiles.cost[0], formatUsd(cost.cost_per_event_usd, 4), tiles.cost[1](formatUsd(cost.total_cost_usd, 2))],
    ]);
    $("#m2p").textContent = ui.m2p(summary.model);
    if (human) $("#m3p").textContent = ui.m3pHuman(human.labeled, ui.labeler(human.labeler));
  }

  /** Renders the footer with the data sources and the last update time. */
  function renderFooter() {
    const updated = new Date(state.index.updated_at).toLocaleString(LOCALES[lang], {
      dateStyle: "short",
      timeStyle: "short",
    });
    $("#footer").replaceChildren(ui.footer(updated), el("a", { href: REPO_URL, text: ui.code }), ".");
  }

  /** Renders the parts of the page that depend on the selected ticker. */
  function renderTicker() {
    $("#finding").textContent = findingText();
    renderPriceFigures();
    paintPins();
  }

  /** Renders every text on the page; called on load and on each language switch. */
  function renderText() {
    document.documentElement.lang = HTML_LANG[lang];
    document.title = ui.brand;
    $('meta[name="description"]').setAttribute("content", ui.metaDesc);
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = ui[node.dataset.i18n];
    });
    document.querySelectorAll(".lang button").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
    });
    $("#tickers").setAttribute("aria-label", ui.tickersLabel);
    $("#chart").setAttribute("aria-label", ui.chartAria);
    renderLegend();
    renderMethod();
    if (state.index) renderFooter();
    if (state.ticker) {
      renderTicker();
      renderDetail();
      renderTable();
      placeCallout();
      chart.applyOptions(chartTheme());
      relayout();
    }
  }

  /** Switches the language, saves it and writes it to the URL so the link can be shared as is. */
  function setLang(next) {
    if (next === lang) return;
    lang = next;
    ui = STRINGS[lang];
    localStorage.setItem("lang", lang);
    const url = new URL(location.href);
    url.searchParams.set("lang", lang);
    history.replaceState(null, "", url);
    renderText();
  }

  /**
   * Selects an event and updates the pins, notes, table and callout.
   *
   * @param {Object|null} event the event to show
   * @param {boolean} focus also zoom the chart around the day and scroll it into view
   */
  function select(event, focus = false) {
    state.selected = event;
    for (const pin of $("#pins").children) pin.classList.toggle("sel", pin.dataset.d === event?.date);
    renderDetail();
    renderTable();
    placeCallout();
    relayout();
    if (focus && event) {
      chart.timeScale().setVisibleRange({
        from: shiftDate(event.date, -FOCUS_WINDOW_DAYS),
        to: shiftDate(event.date, FOCUS_WINDOW_DAYS),
      });
      const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
      $(".plate").scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth" });
    }
  }

  /** Fetches a ticker's prices and events once and keeps them for later switches. */
  async function fetchTicker(ticker) {
    if (!tickerCache[ticker]) {
      const [prices, events] = await Promise.all([
        getJSON(`data/prices/${ticker}.json`),
        getJSON(`data/events/${ticker}.json`).catch(() => []),
      ]);
      tickerCache[ticker] = { prices, events };
    }
    return tickerCache[ticker];
  }

  /**
   * Shows a ticker: its last 12 months and the latest event selected.
   *
   * The price files hold extra older history only as warm-up for the detector,
   * so it is cut here. The ticker goes in the URL hash, keeping ?lang=.
   */
  async function load(ticker) {
    state.ticker = ticker;
    const url = new URL(location.href);
    url.hash = ticker;
    history.replaceState(null, "", url);
    document.querySelectorAll("#tickers button").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.t === ticker));
    });

    const { prices, events } = await fetchTicker(ticker);
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    const from = oneYearAgo.toISOString().slice(0, 10);
    state.prices = prices.filter((price) => price.time >= from);
    state.events = events.filter((event) => event.date >= from);
    state.selected = state.events.at(-1) || null;

    series.setData(state.prices.map((price) => ({ time: price.time, value: price.close })));
    chart.timeScale().fitContent();
    renderTicker();
    select(state.selected);
  }

  /** Builds the ticker tabs from index.json. */
  function renderTickerTabs() {
    const tabs = state.index.tickers.map(({ ticker, name }) => {
      const tab = el("button", { type: "button", "data-t": ticker, "aria-pressed": "false", title: name, text: ticker });
      tab.addEventListener("click", () => load(ticker));
      return tab;
    });
    $("#tickers").replaceChildren(...tabs);
  }

  /** Recolours the chart canvas when the system switches between light and dark mode. */
  function followSystemTheme() {
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      chart.applyOptions(chartTheme());
      series.applyOptions({ color: cssColor("--line") });
    });
  }

  /** Starts the page: texts first, then the data, the chart, the ticker in the URL hash and the eval summary. */
  async function main() {
    if (langFromUrl && STRINGS[langFromUrl]) localStorage.setItem("lang", langFromUrl);
    document.querySelectorAll(".lang button").forEach((button) => {
      button.addEventListener("click", () => setLang(button.dataset.lang));
    });
    renderText();

    try {
      state.index = await getJSON("data/index.json");
    } catch (error) {
      $("#finding").textContent = ui.loadError;
      throw error;
    }
    renderFooter();
    renderTickerTabs();
    buildChart();
    state.ibov = await getJSON(`data/prices/${state.index.index}.json`).catch(() => []);

    const tickerInHash = location.hash.slice(1);
    const known = state.index.tickers.some(({ ticker }) => ticker === tickerInHash);
    await load(known ? tickerInHash : state.index.tickers[0].ticker);

    getJSON("data/eval_summary.json")
      .then((summary) => {
        state.summary = summary;
        renderMethod();
      })
      .catch(() => {});
    followSystemTheme();
  }

  main();
}
