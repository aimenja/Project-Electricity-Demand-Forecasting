const $ = (id) => document.getElementById(id);
const state = { meta: null, profile: null, horizon: 7 };

const fmt = (n, d = 3) =>
  Number(n).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const shortDate = (iso) =>
  new Date(iso + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function setStatus(text, isError = false) {
  const el = $("status");
  el.textContent = text;
  el.className = isError ? "status error" : "status";
}

// ---------------------------------------------------------------- input form

function fieldControl(field) {
  const label = document.createElement("label");
  const name = document.createElement("span");
  name.textContent = field.name;
  label.appendChild(name);

  let input;
  if (field.type === "categorical") {
    input = document.createElement("select");
    for (const option of field.options) {
      const opt = new Option(option, option);
      input.appendChild(opt);
    }
    input.value = field.default ?? field.options[0] ?? "";
  } else {
    input = document.createElement("input");
    input.type = "number";
    input.step = field.integer ? "1" : "any";
    input.min = "0";
    input.value = field.default ?? 0;
  }
  input.dataset.feature = field.name;
  input.dataset.default = input.value;
  label.appendChild(input);
  return label;
}

function renderFields() {
  const household = $("householdFields");
  const appliances = $("applianceFields");
  household.replaceChildren(...state.profile.household_fields.map(fieldControl));
  appliances.replaceChildren(...state.profile.appliance_fields.map(fieldControl));
}

function collectOverrides() {
  const overrides = {};
  for (const el of document.querySelectorAll("[data-feature]")) {
    if (el.value === "") continue;
    overrides[el.dataset.feature] = el.type === "number" ? Number(el.value) : el.value;
  }
  return overrides;
}

function resetFields() {
  for (const el of document.querySelectorAll("[data-feature]")) el.value = el.dataset.default;
}

// ------------------------------------------------------------------ notices

function renderNotices(flags) {
  const host = $("notices");
  if (!flags.length) {
    host.replaceChildren();
    return;
  }
  const box = document.createElement("div");
  box.className = "notice";
  const title = document.createElement("h3");
  title.textContent = "Data quality warning for this house";
  const list = document.createElement("ul");
  for (const flag of flags) {
    const li = document.createElement("li");
    li.textContent = flag;
    list.appendChild(li);
  }
  box.append(title, list);
  host.replaceChildren(box);
}

// --------------------------------------------------------------------- KPIs

function kpi(label, value, unit, sub) {
  const card = document.createElement("div");
  card.className = "kpi";
  card.innerHTML = `<div class="k-label"></div><div class="k-value"></div><div class="k-sub"></div>`;
  card.querySelector(".k-label").textContent = label;
  card.querySelector(".k-value").textContent = value;
  if (unit) {
    const u = document.createElement("small");
    u.textContent = unit;
    card.querySelector(".k-value").appendChild(u);
  }
  card.querySelector(".k-sub").textContent = sub || "";
  return card;
}

function renderKpis(result) {
  const days = result.daily.length;
  const cards = [
    kpi(`${days}-day total`, fmt(result.total_kwh), "kWh", `${shortDate(result.daily[0].date)} – ${shortDate(result.daily[days - 1].date)}`),
    kpi("Average per day", fmt(result.average_kwh), "kWh", "Mean predicted daily demand"),
    kpi("Peak day", fmt(result.peak_day.kwh), "kWh", shortDate(result.peak_day.date)),
    kpi("Appliances configured", String(state.profile.appliance_fields.length), "", `${state.profile.auto_filled_feature_count} model features auto-filled`),
  ];
  $("kpis").replaceChildren(...cards);
}

// -------------------------------------------------------------------- chart

const SVG_NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs) => {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};

function renderChart(history, forecast) {
  const svg = $("chart");
  svg.replaceChildren();

  const pad = { top: 16, right: 16, bottom: 34, left: 58 };
  const width = Math.max(640, svg.clientWidth || 720);
  const height = 300;
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);

  const series = [
    ...history.map((d) => ({ ...d, kind: "history" })),
    ...forecast.map((d) => ({ ...d, kind: "forecast" })),
  ];
  if (!series.length) return;

  const maxY = Math.max(...series.map((d) => d.kwh), 1e-6);
  const x = (i) => pad.left + (series.length === 1 ? plotW / 2 : (i * plotW) / (series.length - 1));
  const y = (v) => pad.top + plotH - (v / maxY) * plotH;

  // gridlines + y axis
  for (let t = 0; t <= 4; t++) {
    const value = (maxY * t) / 4;
    const yy = y(value);
    svg.appendChild(el("line", { x1: pad.left, x2: width - pad.right, y1: yy, y2: yy, stroke: "#e6ebf1" }));
    const label = el("text", { x: pad.left - 8, y: yy + 4, "text-anchor": "end", "font-size": "11", fill: "#5d6b7d" });
    label.textContent = value >= 1 ? value.toFixed(1) : value.toFixed(4);
    svg.appendChild(label);
  }

  // forecast region shading
  const splitIndex = history.length;
  if (splitIndex > 0 && forecast.length) {
    svg.appendChild(el("rect", {
      x: x(splitIndex - 0.5 < 0 ? 0 : splitIndex - 1), y: pad.top,
      width: width - pad.right - x(splitIndex - 1), height: plotH,
      fill: "#fdf1e0", opacity: ".55",
    }));
  }

  const line = (points, stroke) => {
    if (points.length < 2) return;
    const d = points.map((p, i) => `${i ? "L" : "M"}${x(p.i).toFixed(2)},${y(p.kwh).toFixed(2)}`).join(" ");
    svg.appendChild(el("path", { d, fill: "none", stroke, "stroke-width": "2", "stroke-linejoin": "round" }));
  };

  const indexed = series.map((d, i) => ({ ...d, i }));
  line(indexed.filter((d) => d.kind === "history"), "#0f766e");
  // join the two lines so the transition is continuous
  const bridge = indexed.slice(Math.max(0, splitIndex - 1)).filter((d) => d.i >= splitIndex - 1);
  line(bridge, "#b45309");

  for (const d of indexed.filter((p) => p.kind === "forecast")) {
    const dot = el("circle", { cx: x(d.i), cy: y(d.kwh), r: "3", fill: "#b45309" });
    const title = el("title", {});
    title.textContent = `${d.date}: ${fmt(d.kwh, 4)} kWh`;
    dot.appendChild(title);
    svg.appendChild(dot);
  }

  // x labels
  const step = Math.max(1, Math.round(series.length / 8));
  for (let i = 0; i < series.length; i += step) {
    const label = el("text", { x: x(i), y: height - 12, "text-anchor": "middle", "font-size": "11", fill: "#5d6b7d" });
    label.textContent = shortDate(series[i].date);
    svg.appendChild(label);
  }
}

// -------------------------------------------------------------- sensitivity

function renderSensitivity(sens) {
  const host = $("sensitivity");
  const rows = sens.rows || [];
  if (!sens.available || !rows.length) {
    host.textContent = "Appliance what-if is unavailable. Run scripts/train_profile_model.py to enable it.";
    return;
  }

  const baseline = document.createElement("p");
  baseline.className = "hint";
  baseline.innerHTML = `Profile-model baseline for this household: <b>${fmt(sens.baseline_kwh, 3)} kWh/day</b>. Each row shows the estimate with one more of that appliance.`;

  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.delta_kwh)), 1e-9);

  const table = document.createElement("table");
  table.innerHTML = `<thead><tr>
      <th>Appliance</th><th class="num">Current count</th>
      <th class="num">Predicted kWh with +1</th><th class="num">Change</th><th>Relative impact</th>
    </tr></thead>`;
  const body = document.createElement("tbody");

  for (const r of rows) {
    const tr = document.createElement("tr");
    const cells = [r.appliance, fmt(r.base_count, 0), fmt(r.plus_one_kwh, 4),
      `${r.delta_kwh >= 0 ? "+" : ""}${fmt(r.delta_kwh, 4)}`];
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      td.textContent = text;
      if (i > 0) td.className = "num";
      if (i === 3 && r.delta_kwh !== 0) td.classList.add(r.delta_kwh > 0 ? "up" : "down");
      tr.appendChild(td);
    });
    const barCell = document.createElement("td");
    const bar = document.createElement("div");
    bar.className = r.delta_kwh < 0 ? "bar down" : "bar";
    const fill = document.createElement("i");
    fill.style.width = `${(Math.abs(r.delta_kwh) / maxAbs) * 100}%`;
    bar.appendChild(fill);
    barCell.appendChild(bar);
    tr.appendChild(barCell);
    body.appendChild(tr);
  }
  table.appendChild(body);
  host.replaceChildren(baseline, table);
}

// -------------------------------------------------------------- model panel

function renderProfileModel(pm) {
  if (!pm) return null;
  const box = document.createElement("div");
  const dl = document.createElement("dl");
  dl.className = "meta";
  const t = pm.metrics.test || {};
  for (const [term, value] of [
    ["What-if model", pm.model],
    ["Purpose", pm.purpose],
    ["Excluded", pm.excluded],
    ["Features", pm.feature_count],
    ["Test performance", t.MAE === undefined ? "n/a" :
      `MAE ${t.MAE.toFixed(4)} · RMSE ${t.RMSE.toFixed(4)} · R² ${t.R2.toFixed(4)} (n=${t.n})`],
  ]) {
    const dt = document.createElement("dt"); dt.textContent = term;
    const dd = document.createElement("dd"); dd.textContent = value;
    dl.append(dt, dd);
  }
  box.appendChild(dl);
  return box;
}

function renderModel(model) {
  $("modelBadge").innerHTML = "";
  const best = model.metrics.find((m) => /xgboost tuned/i.test(m.model)) || model.metrics[0];
  if (best) {
    for (const [k, v] of [["MAE", best.MAE], ["RMSE", best.RMSE], ["R²", best.R2]]) {
      const box = document.createElement("div");
      box.innerHTML = `<b></b>${k}`;
      box.querySelector("b").textContent = Number(v).toFixed(4);
      $("modelBadge").appendChild(box);
    }
  }

  const dl = document.createElement("dl");
  dl.className = "meta";
  const entries = [
    ["Model", model.model],
    ["Target", model.target],
    ["Model features", model.feature_count],
    ["Training data", `${model.data_start} to ${model.data_end}`],
    ["Train/test split", `train ends ${model.train_end_date}`],
    ["Coverage", `${model.house_count} houses across ${model.city_count} cities`],
    ["Hyperparameters", Object.entries(model.best_parameters).map(([k, v]) => `${k}=${v}`).join(", ")],
  ];
  for (const [term, value] of entries) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    dl.append(dt, dd);
  }

  const table = document.createElement("table");
  table.innerHTML = `<thead><tr><th>Model comparison</th><th class="num">MAE</th><th class="num">RMSE</th><th class="num">R²</th></tr></thead>`;
  const body = document.createElement("tbody");
  for (const m of model.metrics) {
    const tr = document.createElement("tr");
    for (const [i, v] of [m.model, m.MAE, m.RMSE, m.R2].entries()) {
      const td = document.createElement("td");
      td.textContent = i === 0 ? v : Number(v).toFixed(4);
      if (i > 0) td.className = "num";
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
  table.appendChild(body);

  const note = document.createElement("p");
  note.className = "hint";
  note.style.marginTop = "14px";
  note.textContent =
    "Future weather is approximated from a historical seasonal average for the selected city. " +
    "It is not a real weather forecast, so longer horizons carry more uncertainty.";

  const children = [dl, document.createElement("br"), table, note];
  const profile = renderProfileModel(state.meta && state.meta.profile_model);
  if (profile) {
    const hr = document.createElement("hr");
    hr.style.cssText = "border:none;border-top:1px solid var(--line);margin:18px 0";
    children.push(hr, profile);
  }
  $("modelInfo").replaceChildren(...children);
}

// ------------------------------------------------------------------ actions

async function loadHouse() {
  const city = $("city").value;
  const house = $("house").value;
  setStatus("Loading household profile…");
  state.profile = await api(`/api/house/${encodeURIComponent(city)}/${encodeURIComponent(house)}`);
  $("startDate").value = state.profile.default_start_date;
  $("startDate").min = state.profile.default_start_date;
  renderFields();
  renderNotices(state.profile.data_quality.flags);
  setStatus(`History available through ${state.profile.latest_date}.`);
}

async function runForecast() {
  const button = $("run");
  button.disabled = true;
  setStatus("Running forecast…");
  try {
    const result = await api("/api/forecast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city: $("city").value,
        house: $("house").value,
        start_date: $("startDate").value,
        horizon: state.horizon,
        overrides: collectOverrides(),
      }),
    });
    renderKpis(result);
    renderChart(state.profile.history.slice(-30), result.daily);
    renderSensitivity(result.sensitivity);
    setStatus(`Forecast ready — ${result.daily.length} day(s) predicted.`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    button.disabled = false;
  }
}

function populateHouses(city) {
  const houses = state.meta.houses_by_city[city] || [];
  $("house").replaceChildren(...houses.map((h) => new Option(h, h)));
}

async function init() {
  try {
    state.meta = await api("/api/meta");
  } catch (err) {
    setStatus(`Could not reach the API: ${err.message}`, true);
    return;
  }
  renderModel(state.meta.model);

  $("city").replaceChildren(...state.meta.cities.map((c) => new Option(c, c)));
  $("city").value = state.meta.default.city;
  populateHouses($("city").value);
  $("house").value = state.meta.default.house;

  $("city").addEventListener("change", async () => {
    populateHouses($("city").value);
    await loadHouse();
  });
  $("house").addEventListener("change", loadHouse);
  $("run").addEventListener("click", runForecast);
  $("reset").addEventListener("click", resetFields);

  $("horizon").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-days]");
    if (!button) return;
    state.horizon = Number(button.dataset.days);
    for (const b of $("horizon").querySelectorAll("button")) {
      b.setAttribute("aria-pressed", String(b === button));
    }
  });

  window.addEventListener("resize", () => {
    if (state.lastResult) renderChart(state.profile.history.slice(-30), state.lastResult.daily);
  });

  await loadHouse();
  await runForecast();
}

init();
