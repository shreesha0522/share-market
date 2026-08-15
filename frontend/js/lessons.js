import { API_BASE } from "./utils.js";

export async function loadInvestorLessons() {
  const grid = document.getElementById("lessonsGrid");
  if (!grid) return;

  const lessons = [];

  try {
    const [summaryRes, corrRes] = await Promise.all([
      fetch(`${API_BASE}/market/summary`),
      fetch(`${API_BASE}/market/correlation`),
    ]);
    if (summaryRes.ok && corrRes.ok) {
      const summary = await summaryRes.json();
      const corr = await corrRes.json();

      const sectorsByVol = [...summary.sector_metrics].sort((a, b) => b.avg_volatility_pct - a.avg_volatility_pct);
      const mostVol = sectorsByVol[0];
      lessons.push({
        title: "Know a sector's volatility before you enter it",
        text: `${mostVol.sector} showed the highest average volatility in this dataset (${mostVol.avg_volatility_pct}%). Higher volatility means bigger swings in both directions — size any position accordingly, and don't mistake a volatile stock for a bad one, or a calm one for a safe one.`,
      });

      let maxPair = null;
      corr.tickers.forEach((t1) => {
        corr.tickers.forEach((t2) => {
          if (t1 >= t2) return;
          const v = corr.matrix[t1]?.[t2];
          if (v === null || v === undefined) return;
          if (!maxPair || v > maxPair.v) maxPair = { t1, t2, v };
        });
      });
      if (maxPair && maxPair.v > 0.4) {
        lessons.push({
          title: "Owning more stocks isn't automatically diversification",
          text: `${maxPair.t1} and ${maxPair.t2} moved together with a correlation of ${maxPair.v.toFixed(2)} in this dataset. Holding both doesn't spread your risk as much as it might feel like — real diversification means picking companies that don't move in lockstep.`,
        });
      }

      const negCount = summary.company_metrics.filter((c) => c.total_return_pct < 0).length;
      if (negCount > 0) {
        const pctNeg = Math.round((negCount / summary.company_metrics.length) * 100);
        lessons.push({
          title: "Losses are a real possibility, not an edge case",
          text: `${pctNeg}% of the companies tracked in this study posted a negative return over the 5-year window. Only invest money you won't need in the short term, and go in expecting that losses are a normal part of the process, not a sign you did something wrong.`,
        });
      }
    }
  } catch (err) {
    // market side is best-effort for this section
  }

  try {
    const surveyRes = await fetch(`${API_BASE}/survey/summary`);
    if (surveyRes.ok) {
      const survey = await surveyRes.json();

      if (survey.ranked_challenges && survey.ranked_challenges.length) {
        const top = survey.ranked_challenges[0];
        lessons.push({
          title: `Address "${top.challenge}" before you start`,
          text: `This was the highest-rated challenge among surveyed investors (avg ${top.avg_score}/5). If this feels familiar, it's worth deliberately working on before putting in significant capital — it's a shared, common starting point, not a personal shortcoming.`,
        });
      }

      const withData = (survey.by_experience || []).filter((e) => e.avg_challenge_score != null);
      if (withData.length >= 2) {
        const sorted = [...withData].sort((a, b) => b.avg_challenge_score - a.avg_challenge_score);
        const highest = sorted[0];
        const lowest = sorted[sorted.length - 1];
        if (highest.avg_challenge_score > lowest.avg_challenge_score) {
          lessons.push({
            title: "The challenges genuinely get easier with time",
            text: `Investors with "${lowest.experience}" reported lower challenge scores than those with "${highest.experience}" in this sample. Early difficulty is normal and, based on this data, tends to ease with experience — it's worth pushing through the learning curve rather than reading it as a sign to stop.`,
          });
        }
      }

      if (survey.n_respondents && survey.n_respondents < 30) {
        lessons.push({
          title: "A note on this data",
          text: `These survey-based lessons are currently drawn from ${survey.n_respondents} respondent${survey.n_respondents === 1 ? "" : "s"}. Treat them as directional early signals rather than definitive conclusions until the sample grows.`,
        });
      }
    }
  } catch (err) {
    // survey side is best-effort too
  }

  if (lessons.length === 0) {
    grid.innerHTML = `<div class="lesson-card"><p class="lesson-text">Not enough data yet to generate lessons.</p></div>`;
    return;
  }

  grid.innerHTML = lessons
    .map(
      (l, i) => `
      <div class="lesson-card">
        <span class="lesson-num">${String(i + 1).padStart(2, "0")}</span>
        <h3 class="lesson-title">${l.title}</h3>
        <p class="lesson-text">${l.text}</p>
      </div>`
    )
    .join("");
}
