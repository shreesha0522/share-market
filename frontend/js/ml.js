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
  const k = reg.cv_folds ?? cls.cv_folds;

  if (!n) {
    el.hidden = true;
    return;
  }

  el.hidden = false;
  if (!k) {
    el.textContent = `Note: with only ${n} respondents, there wasn't enough data for cross-validated evaluation. Treat any figures shown as illustrative only.`;
  } else {
    el.textContent = `Note: metrics below use ${k}-fold cross-validation across all ${n} respondents (mean ± standard deviation across folds), rather than a single train/test split — but with a sample this small, treat these figures as directional early signals, not conclusive results.`;
  }
}

function renderRegression(reg) {
  const grid = document.getElementById("regStatsGrid");
  if (!grid) return;

  if (reg.error) {
    grid.innerHTML = `<div class="stat-card"><div class="stat-note">${reg.error}</div></div>`;
    return;
  }

  const rf = reg.random_forest;
  const lin = reg.linear_regression_baseline;

  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Random Forest R² (${reg.cv_folds}-fold CV)</div>
      <div class="stat-value">${rf.r_squared_mean} ± ${rf.r_squared_std}</div>
      <div class="stat-note">MAE: ${rf.mae_mean} ± ${rf.mae_std}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Linear Regression R² (baseline)</div>
      <div class="stat-value">${lin.r_squared_mean} ± ${lin.r_squared_std}</div>
      <div class="stat-note">MAE: ${lin.mae_mean} ± ${lin.mae_std}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Sample Size</div>
      <div class="stat-value">${reg.n_samples}</div>
      <div class="stat-note">${reg.n_imputed_sector_exposure ? `${reg.n_imputed_sector_exposure} had imputed sector exposure` : "All respondents matched tracked sectors"}</div>
    </div>
  `;

  const entries = Object.entries(rf.feature_importance).sort((a, b) => b[1] - a[1]);

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
      <div class="stat-label">Accuracy (${cls.cv_folds}-fold CV)</div>
      <div class="stat-value">${(cls.accuracy_mean * 100).toFixed(0)}% ± ${(cls.accuracy_std * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Precision</div>
      <div class="stat-value">${(cls.precision_mean * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Recall</div>
      <div class="stat-value">${(cls.recall_mean * 100).toFixed(0)}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">F1 Score</div>
      <div class="stat-value">${cls.f1_mean} ± ${cls.f1_std}</div>
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

export async function setupPredictionForm() {
  const form = document.getElementById("predictForm");
  const sectorSelect = document.getElementById("pSector");
  const resultEl = document.getElementById("predictResult");
  if (!form || !sectorSelect || !resultEl) return;

  try {
    const res = await fetch(`${API_BASE}/market/summary`);
    if (res.ok) {
      const data = await res.json();
      sectorSelect.innerHTML = (data.sector_metrics || [])
        .map((s) => `<option value="${s.sector}">${s.sector}</option>`)
        .join("");
    }
  } catch (err) {
    sectorSelect.innerHTML = `<option value="">Couldn't load sectors</option>`;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const experience = document.getElementById("pExperience").value;
    const portfolio = document.getElementById("pPortfolio").value;
    const tradeFreq = document.getElementById("pTradeFreq").value;
    const sector = sectorSelect.value;

    resultEl.className = "readiness-result show";
    resultEl.innerHTML = `<p>Running prediction…</p>`;

    const params = new URLSearchParams({ experience, portfolio, trade_freq: tradeFreq, sector });

    try {
      const res = await fetch(`${API_BASE}/survey/ml/predict?${params}`);
      const data = await res.json();

      if (!res.ok || data.error) {
        resultEl.className = "readiness-result show mismatch";
        resultEl.innerHTML = `<p class="result-title mismatch">Couldn't run the prediction</p><p>${data.error || friendlyFetchError(new Error())}</p>`;
        return;
      }

      const labelText = data.predicted_label === "high_challenge" ? "above-average challenge" : "below-average challenge";
      const cssClass = data.predicted_label === "high_challenge" ? "mismatch" : "match";
      const confidenceText = data.confidence !== null && data.confidence !== undefined
        ? ` (model confidence: ${(data.confidence * 100).toFixed(0)}%)`
        : "";

      resultEl.className = `readiness-result show ${cssClass}`;
      resultEl.innerHTML = `
        <p class="result-title ${cssClass}">Predicted challenge score: ${data.predicted_challenge_score} / 5</p>
        <p>
          Based on this profile, the model predicts <strong>${labelText}</strong> relative to
          other respondents${confidenceText}. For comparison, the survey sample's average
          overall challenge score is <strong>${data.sample_average_score}</strong> and the
          median is <strong>${data.sample_median_score}</strong>.
        </p>
        <p style="opacity: 0.75; font-size: 0.9em;">
          Trained on ${data.n_training_samples} survey respondents — with a sample this small,
          treat this as an illustrative estimate, not a validated forecast.
        </p>
      `;
    } catch (err) {
      resultEl.className = "readiness-result show mismatch";
      resultEl.innerHTML = `<p class="result-title mismatch">Couldn't run the prediction</p><p>${friendlyFetchError(err)}</p>`;
    }
  });
}
