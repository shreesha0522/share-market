const API_BASE = "http://127.0.0.1:5000/api";

const CHART_COLORS = {
  accent: "#D4A24E",
  red: "#C4554D",
  green: "#4E9B6E",
  purple: "#8A7CC7",
  muted: "#8B96A3",
  grid: "#2A3441",
  text: "#E8EAED",
};

Chart.defaults.color = CHART_COLORS.muted;
Chart.defaults.borderColor = CHART_COLORS.grid;
Chart.defaults.font.family = "IBM Plex Mono, monospace";

let mainChart = null;
let currentChartType = "volatility";
let currentTickerData = null;

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

document.querySelectorAll(".chart-tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".chart-tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentChartType = btn.dataset.chart;
    if (currentTickerData) renderMainChart(currentTickerData);
  });
});

async function init() {
  await loadTickerList();
  await loadTickerView();
  await loadMarketSummaryTable();
  await loadSurveySummary();
  await loadSurveyStats();

  document.getElementById("loadBtn").addEventListener("click", loadTickerView);
}

async function loadTickerList() {
  const track = document.getElementById("tickerTrack");
  const select = document.getElementById("tickerSelect");

  try {
    const res = await fetch(`${API_BASE}/tickers`);
    if (!res.ok) throw new Error("Couldn't load ticker list.");
    const tickers = await res.json();

    select.innerHTML = tickers
      .map((t) => `<option value="${t.ticker}">${t.ticker} — ${t.sector}</option>`)
      .join("");
    select.value = "NABIL";

    const items = tickers.map((t) => `<span class="ticker-item">${t.ticker} · ${t.sector}</span>`);
    track.innerHTML = items.concat(items).join("");
  } catch (err) {
    track.innerHTML = `<span class="ticker-item">${friendlyFetchError(err)}</span>`;
    select.innerHTML = `<option value="">No companies available</option>`;
    showError("marketError", friendlyFetchError(err));
    showLoading("marketLoading", false);
  }
}

function showLoading(id, isLoading) {
  document.getElementById(id).hidden = !isLoading;
}

function showError(id, message) {
  const el = document.getElementById(id);
  if (!message) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.hidden = false;
  el.textContent = message;
}

function friendlyFetchError(err) {
  if (err instanceof TypeError) {
    return "Couldn't reach the server. Make sure the Flask backend is running on http://127.0.0.1:5000.";
  }
  return err.message || "Something went wrong loading this data.";
}

async function loadTickerView() {
  const ticker = document.getElementById("tickerSelect").value;
  const start = document.getElementById("startDate").value;
  const end = document.getElementById("endDate").value;

  showError("marketError", null);
  showLoading("marketLoading", true);
  document.getElementById("summaryCards").innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/market/${ticker}?start=${start}&end=${end}`);

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const msg = body.error || `No data available for ${ticker} in that date range.`;
      showError("marketError", msg);
      currentTickerData = null;
      if (mainChart) { mainChart.destroy(); mainChart = null; }
      return;
    }

    const data = await res.json();
    currentTickerData = data;
    renderSummaryCards(data.summary);
    renderMainChart(data);
  } catch (err) {
    showError("marketError", friendlyFetchError(err));
    currentTickerData = null;
  } finally {
    showLoading("marketLoading", false);
  }
}

function renderSummaryCards(summary) {
  const ddClass = summary.max_drawdown !== null && summary.max_drawdown < -0.2 ? "neg" : "accent";
  document.getElementById("summaryCards").innerHTML = `
    <div class="summary-card">
      <div class="card-label">${summary.ticker} — Sector</div>
      <div class="card-value accent">${summary.sector}</div>
    </div>
    <div class="summary-card">
      <div class="card-label">Latest Close</div>
      <div class="card-value">Rs. ${summary.latest_close}</div>
    </div>
    <div class="summary-card">
      <div class="card-label">Avg Volatility (30d)</div>
      <div class="card-value">${summary.avg_volatility ?? "—"}</div>
    </div>
    <div class="summary-card">
      <div class="card-label">Max Drawdown</div>
      <div class="card-value ${ddClass}">${summary.max_drawdown !== null ? (summary.max_drawdown * 100).toFixed(1) + "%" : "—"}</div>
    </div>
    <div class="summary-card">
      <div class="card-label">Volume Spike Days</div>
      <div class="card-value">${summary.volume_spike_days}</div>
    </div>
  `;
}

const CHART_CAPTIONS = {
  volatility: "30-day rolling volatility. Higher swings mean it's harder for a new investor to judge whether a price move is noise or a real trend.",
  drawdown: "Drawdown shows how far the price has fallen from its most recent peak — the metric that actually triggers panic-selling.",
  trend: "Price with 20-day and 50-day moving averages, used to separate real trend from short-term noise.",
  volume: "Days where trading volume exceeded 2× its 20-day average, a proxy for FOMO buying or panic selling.",
};

function renderMainChart(data) {
  document.getElementById("chartCaption").textContent = CHART_CAPTIONS[currentChartType];

  const ctx = document.getElementById("mainChart").getContext("2d");
  if (mainChart) mainChart.destroy();

  const s = data.series;
  let datasets, yLabel;

  if (currentChartType === "volatility") {
    datasets = [{ label: "30d Volatility", data: s.volatility_30d, borderColor: CHART_COLORS.accent, borderWidth: 1.6, pointRadius: 0, tension: 0.15 }];
    yLabel = "Volatility";
  } else if (currentChartType === "drawdown") {
    datasets = [{ label: "Drawdown", data: s.drawdown, borderColor: CHART_COLORS.red, borderWidth: 1.6, pointRadius: 0, fill: true, backgroundColor: "rgba(196,85,77,0.12)", tension: 0.1 }];
    yLabel = "Drawdown";
  } else if (currentChartType === "trend") {
    datasets = [
      { label: "Close", data: s.close, borderColor: "rgba(232,234,237,0.35)", borderWidth: 1, pointRadius: 0 },
      { label: "MA 20", data: s.ma_20, borderColor: CHART_COLORS.accent, borderWidth: 1.6, pointRadius: 0 },
      { label: "MA 50", data: s.ma_50, borderColor: CHART_COLORS.purple, borderWidth: 1.6, pointRadius: 0 },
    ];
    yLabel = "Price (NPR)";
  } else {
    datasets = [{
      label: "Volume",
      data: s.volume,
      backgroundColor: s.volume_spike.map((sp) => (sp ? CHART_COLORS.red : "rgba(212,162,78,0.35)")),
      type: "bar",
    }];
    yLabel = "Traded Quantity";
  }

  mainChart = new Chart(ctx, {
    type: currentChartType === "volume" ? "bar" : "line",
    data: { labels: s.dates, datasets },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { color: CHART_COLORS.grid } },
        y: { title: { display: true, text: yLabel, color: CHART_COLORS.muted }, grid: { color: CHART_COLORS.grid } },
      },
      plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
    },
  });
}

async function loadMarketSummaryTable() {
  const tbody = document.querySelector("#companyTable tbody");
  try {
    const res = await fetch(`${API_BASE}/market/summary`);
    if (!res.ok) throw new Error("Couldn't load the company overview table.");
    const data = await res.json();
    tbody.innerHTML = data.company_metrics
      .map((r) => {
        const retClass = r.total_return_pct >= 0 ? "pos" : "neg";
        return `<tr>
          <td>${r.ticker}</td>
          <td>${r.sector}</td>
          <td>Rs. ${r.start_price}</td>
          <td>Rs. ${r.latest_price}</td>
          <td class="${retClass}">${r.total_return_pct}%</td>
          <td>${r.volatility_pct}%</td>
          <td>${Number(r.avg_daily_volume).toLocaleString()}</td>
        </tr>`;
      })
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color: var(--text-muted);">${friendlyFetchError(err)}</td></tr>`;
  }
}

async function loadSurveySummary() {
  showError("surveyError", null);
  showLoading("surveyLoading", true);

  let data;
  try {
    const res = await fetch(`${API_BASE}/survey/summary`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      showError("surveyError", body.error || "Survey data isn't available right now.");
      return;
    }
    data = await res.json();
  } catch (err) {
    showError("surveyError", friendlyFetchError(err));
    return;
  } finally {
    showLoading("surveyLoading", false);
  }

  document.getElementById("syntheticBanner").hidden = !data.is_synthetic;
  document.getElementById("respondentCount").textContent = `Based on ${data.n_respondents} respondents`;

  new Chart(document.getElementById("challengeChart"), {
    type: "bar",
    data: {
      labels: data.ranked_challenges.map((c) => c.challenge),
      datasets: [{ label: "Avg score (1-5)", data: data.ranked_challenges.map((c) => c.avg_score), backgroundColor: CHART_COLORS.accent }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      scales: { x: { min: 0, max: 5, grid: { color: CHART_COLORS.grid } }, y: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  new Chart(document.getElementById("experienceChart"), {
    type: "bar",
    data: {
      labels: data.by_experience.map((r) => r.experience),
      datasets: [{ label: "Avg challenge score", data: data.by_experience.map((r) => r.avg_challenge_score), backgroundColor: CHART_COLORS.purple }],
    },
    options: {
      responsive: true,
      scales: { y: { min: 0, max: 5, grid: { color: CHART_COLORS.grid } }, x: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  const profitLabels = Object.keys(data.profitability_pct);
  new Chart(document.getElementById("profitChart"), {
    type: "doughnut",
    data: {
      labels: profitLabels,
      datasets: [{
        data: profitLabels.map((k) => data.profitability_pct[k]),
        backgroundColor: [CHART_COLORS.green, CHART_COLORS.red, CHART_COLORS.accent, CHART_COLORS.muted],
        borderColor: "#161D26",
        borderWidth: 2,
      }],
    },
    options: { responsive: true, plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } } } },
  });
}

async function loadSurveyStats() {
  let data;
  try {
    const res = await fetch(`${API_BASE}/survey/stats`);
    if (!res.ok) return;
    data = await res.json();
  } catch (err) {
    return;
  }

  const expCorr = data.experience_vs_challenge_correlation;
  const volCorr = data.volatility_vs_perceived_difficulty_correlation;
  const reg = data.regression;

  document.getElementById("statsGrid").innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Experience vs. Challenge Score</div>
      <div class="stat-value">r = ${expCorr.r}</div>
      <div class="stat-note">p = ${expCorr.p_value} — ${Math.abs(expCorr.r) > 0.3 ? "meaningful negative correlation: more experience, fewer reported challenges." : "weak relationship."}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Sector Volatility vs. Perceived Difficulty</div>
      <div class="stat-value">r = ${volCorr.r}</div>
      <div class="stat-note">p = ${volCorr.p_value}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Regression R²</div>
      <div class="stat-value">${reg.r_squared}</div>
      <div class="stat-note">Predictors: experience, portfolio size, trade frequency.</div>
    </div>
  `;
}

init();
