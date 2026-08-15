import { API_BASE, CHART_COLORS, showLoading, showError, friendlyFetchError } from "./utils.js";

export async function loadSurveySummary() {
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

export async function loadSectorLinkage() {
  try {
    const res = await fetch(`${API_BASE}/survey/linkage`);
    if (!res.ok) return;
    const data = await res.json();
    const linkage = data.linkage;

    new Chart(document.getElementById("linkageChart"), {
      type: "bar",
      data: {
        labels: linkage.map((r) => r.sector),
        datasets: [
          {
            label: "Real Volatility (%)",
            data: linkage.map((r) => r.real_volatility_pct),
            backgroundColor: CHART_COLORS.accent,
            yAxisID: "y",
          },
          {
            label: "Perceived Difficulty (1-5)",
            data: linkage.map((r) => r.perceived_difficulty),
            backgroundColor: CHART_COLORS.purple,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Real Volatility (%)", color: CHART_COLORS.accent },
            grid: { color: CHART_COLORS.grid },
          },
          y1: {
            type: "linear",
            position: "right",
            min: 0,
            max: 5,
            title: { display: true, text: "Perceived Difficulty (1-5)", color: CHART_COLORS.purple },
            grid: { drawOnChartArea: false },
          },
          x: { grid: { display: false } },
        },
        plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
      },
    });
  } catch (err) {
    // Silently skip — this is a supplementary chart, not critical path.
  }
}

export async function loadSurveyStats() {
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
