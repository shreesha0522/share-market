import { CHART_COLORS } from "./utils.js";
import { loadTickerList, loadTickerView, loadMarketSummaryTable, loadCorrelationTable, loadComparisonChart, loadKeyFindings, setupChartTabs } from "./market.js";
import { loadSurveySummary, loadSectorLinkage, loadSurveyStats } from "./survey.js";

Chart.defaults.color = CHART_COLORS.muted;
Chart.defaults.borderColor = CHART_COLORS.grid;
Chart.defaults.font.family = "IBM Plex Mono, monospace";

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

setupChartTabs();

const printBtn = document.getElementById("printBtn");
if (printBtn) {
  printBtn.addEventListener("click", () => window.print());
}

async function init() {
  await loadTickerList();
  await loadTickerView();
  await loadMarketSummaryTable();
  await loadCorrelationTable();
  await loadKeyFindings();
  await loadSurveySummary();
  await loadSurveyStats();
  await loadSectorLinkage();

  document.getElementById("loadBtn").addEventListener("click", loadTickerView);
  document.getElementById("compareBtn").addEventListener("click", loadComparisonChart);
}

init();
