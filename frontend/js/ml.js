import { API_BASE, CHART_COLORS, showLoading, showError, friendlyFetchError } from "./utils.js";

let regChart = null;
let clsChart = null;

const FEATURE_LABELS = {
  experience_ordinal: "Investing experience",
  portfolio_ordinal: "Portfolio size",
  trade_freq_ordinal: "Trade frequency",
  exposure_volatility: "Sector volatility exposure",
};

export async function loadMLPredictions() {
  showError("mlError", null);
  showLoading("mlLoading", true);

  let data;
  try {
    const res = await fetch(`${API_BASE}/survey/ml`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      showError("mlError", body.error || "ML results aren't available right now.");
      return;
    }
    data = await res.json();
  } catch (err) {
    showError("mlError", friendlyFetchError(err));
    return;
  } finally {
    showLoading("mlLoading", false);
  }

  document.getElementById("mlSyntheticBanner").hidden = !data.is_synthetic;

  renderRegression(data.challenge_score_prediction);
  renderClassification(data.high_challenge_classification);
  renderCaveat(data.challenge_score_prediction, data.high_challenge_classification);
}

function renderCaveat(reg, cls) {
  const el = document.getElementById("mlCaveat");
  if (!el) return;

  const n = reg.n_samples ?? cls.n_samples;
  const usedHoldout = reg.used_holdout_test_set;

  if (!n) {
    el.hidden = true;
    return;
  }

  el.hidden = false;
  if (!usedHoldout) {
    el.textContent = `Note: with only ${n} respondents, the model was trained on the full sample rather than a held-out test set — the metrics below reflect fit on training data, not out-of-sample accuracy. Treat them as directional, not conclusive.`;
  } else {
    el.textContent = `Note: metrics below are evaluated on a held-out test set of just ${reg.test_set_size ?? cls.test_set_size} respondents (out of ${n} total). With a sample this small, treat these figures as directional early signals, not conclusive results.`;
  }
}

function renderRegression(reg) {
  const grid = document.getElementById("regStatsGrid");
  if (!grid) return;

  if (reg.error) {
    grid.innerHTML = `<div class="stat-card"><div class="stat-note">${reg.error}</div></div>`;
    return;
  }

  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Random Forest R²</div>
      <div class="stat-value">${reg.random_forest.r_squared}</div>
      <div class="stat-note">MAE: ${reg.random_forest.mae}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Linear Regression R² (baseline)</div>
      <div class="stat-value">${reg.linear_regression_baseline.r_squared}</div>
      <div class="stat-note">MAE: ${reg.linear_regression_baseline.mae}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Sample Size</div>
      <div class="stat-value">${reg.n_samples}</div>
      <div class="stat-note">Test set: ${reg.test_set_size} respondent${reg.test_set_size === 1 ? "" : "s"}</div>
    </div>
  `;

  const entries = Object.entries(reg.random_forest.feature_importance).sort((a, b) => b[1] - a[1]);

  if (regChart) regChart.destroy();
  regChart = new Chart(document.getElementById("regFeatureChart"), {
    type: "bar",
    data: {
      labels: entries.map(([k]) => FEATURE_LABELS[k] || k),
      datasets: [{ label: "Feature Importance", data: entries.map(([, v]) => v), backgroundColor: CHART_COLORS.accent }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      scales: { x: { min: 0, grid: { color: CHART_COLORS.grid } }, y: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });
}

function renderClassification(cls) {
  const grid = document.getElementById("clsStatsGrid");
  if (!grid) return;

  if (cls.error) {
    grid.innerHTML = `<div class="stat-card"><div class="stat-note">${cls.error}</div></div>`;
    document.getElementById("confusionMatrixTable").innerHTML = "";
    return;
  }

  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Accuracy</div>
      <div class="stat-value">${(cls.accuracy * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Precision</div>
      <div class="stat-value">${(cls.precision * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Recall</div>
      <div class="stat-value">${(cls.recall * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">F1 Score</div>
      <div class="stat-value">${cls.f1}</div>
      <div class="stat-note">Median score used as the high/low cutoff: ${cls.median_challenge_score}</div>
    </div>
  `;

  const entries = Object.entries(cls.feature_importance).sort((a, b) => b[1] - a[1]);

  if (clsChart) clsChart.destroy();
  clsChart = new Chart(document.getElementById("clsFeatureChart"), {
    type: "bar",
    data: {
      labels: entries.map(([k]) => FEATURE_LABELS[k] || k),
      datasets: [{ label: "Feature Importance", data: entries.map(([, v]) => v), backgroundColor: CHART_COLORS.purple }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      scales: { x: { min: 0, grid: { color: CHART_COLORS.grid } }, y: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  const [labelsLow, labelsHigh] = cls.confusion_matrix.labels;
  const [[tn, fp], [fn, tp]] = cls.confusion_matrix.matrix;

  document.getElementById("confusionMatrixTable").innerHTML = `
    <thead>
      <tr><th></th><th>Predicted: ${labelsLow}</th><th>Predicted: ${labelsHigh}</th></tr>
    </thead>
    <tbody>
      <tr><th>Actual: ${labelsLow}</th><td>${tn}</td><td>${fp}</td></tr>
      <tr><th>Actual: ${labelsHigh}</th><td>${fn}</td><td>${tp}</td></tr>
    </tbody>
  `;
}
