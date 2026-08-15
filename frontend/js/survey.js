import { API_BASE, CHART_COLORS, showLoading, showError, friendlyFetchError } from "./utils.js";

let _summary = null;
let _stats = null;
let _linkage = null;

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

  new Chart(document.getElementById("ageChart"), {
    type: "bar",
    data: {
      labels: data.by_age.map((r) => r.segment),
      datasets: [{ label: "Avg challenge score", data: data.by_age.map((r) => r.avg_challenge_score), backgroundColor: CHART_COLORS.green }],
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

  _summary = data;
  renderKeyFindings();
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
    _linkage = linkage;
    renderKeyFindings();
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

  _stats = data;
  renderKeyFindings();
}

const PREDICTOR_LABELS = {
  experience_ordinal: "investing experience",
  portfolio_ordinal: "portfolio size",
  trade_freq_ordinal: "trade frequency",
};

function renderKeyFindings() {
  const el = document.getElementById("keyFindings");
  if (!el) return;
  if (!_summary || !_stats) {
    el.innerHTML = `<p class="finding-empty">Findings will appear once survey data has loaded.</p>`;
    return;
  }

  const points = [];

  const top = _summary.ranked_challenges[0];
  if (top) {
    points.push(
      `The most widely reported challenge among ${_summary.n_respondents} respondents is <strong>${top.challenge}</strong> (avg score ${top.avg_score}/5).`
    );
  }

  const exp = _stats.experience_vs_challenge_correlation;
  if (exp) {
    const strength = Math.abs(exp.r) > 0.5 ? "strong" : Math.abs(exp.r) > 0.3 ? "moderate" : "weak";
    const direction = exp.r < 0 ? "fewer" : "more";
    const sig = exp.p_value < 0.05 ? "statistically significant" : "not statistically significant at the 0.05 level";
    points.push(
      `Investing experience shows a ${strength} correlation with reported challenges (r = ${exp.r}, ${sig}) — more experienced investors tend to report ${direction} challenges overall.`
    );
  }

  const vol = _stats.volatility_vs_perceived_difficulty_correlation;
  if (vol) {
    const tracks = Math.abs(vol.r) > 0.4;
    points.push(
      tracks
        ? `Perceived difficulty tracks real market volatility reasonably well (r = ${vol.r}), suggesting respondents can broadly distinguish riskier sectors.`
        : `Perceived difficulty only weakly tracks real market volatility (r = ${vol.r}), suggesting many respondents are not accurately distinguishing higher-risk sectors from lower-risk ones.`
    );
  }

  if (_linkage && _linkage.length > 0) {
    const withGap = _linkage.map((r) => ({
      ...r,
      gap: (r.real_volatility_pct / Math.max(...(_linkage.map((x) => x.real_volatility_pct)))) -
           (r.perceived_difficulty / 5),
    }));
    const underrated = withGap.reduce((a, b) => (b.gap > a.gap ? b : a));
    if (underrated.gap > 0.15) {
      points.push(
        `<strong>${underrated.sector}</strong> stands out as a sector where real volatility (${underrated.real_volatility_pct}%) is high relative to how difficult respondents rated it (${underrated.perceived_difficulty}/5) — a potential blind spot for new investors.`
      );
    }
  }

  const reg = _stats.regression;
  if (reg) {
    const sigPredictors = Object.entries(reg.coefficients)
      .filter(([name, c]) => name !== "const" && c.p_value < 0.05)
      .sort((a, b) => Math.abs(b[1].coef) - Math.abs(a[1].coef));
    if (sigPredictors.length > 0) {
      const [name, c] = sigPredictors[0];
      points.push(
        `In the regression model (R² = ${reg.r_squared}), <strong>${PREDICTOR_LABELS[name] || name}</strong> is the strongest significant predictor of overall challenge score (coef = ${c.coef}, p = ${c.p_value}).`
      );
    } else {
      points.push(
        `In the regression model (R² = ${reg.r_squared}), none of the three predictors reached statistical significance at the 0.05 level — overall challenge score may be driven more by factors not captured in this survey.`
      );
    }
  }

  if (_summary.is_synthetic) {
    points.push(
      `<em>Note: these findings are currently based on synthetic placeholder data and should not be cited until real survey responses replace it.</em>`
    );
  }

  el.innerHTML = `<ul>${points.map((p) => `<li>${p}</li>`).join("")}</ul>`;
}
