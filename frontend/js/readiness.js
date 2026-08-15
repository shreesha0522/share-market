import { API_BASE } from "./utils.js";

const RISK_TOLERANCE = {
  sell: { label: "Low risk tolerance", maxVolatility: 1.7 },
  hold: { label: "Medium risk tolerance", maxVolatility: 2.3 },
  buy: { label: "High risk tolerance", maxVolatility: Infinity },
};

export async function setupReadinessCheck() {
  const form = document.getElementById("readinessForm");
  const sectorSelect = document.getElementById("rSector");
  const resultEl = document.getElementById("readinessResult");
  if (!form || !sectorSelect || !resultEl) return;

  let sectorMetrics = [];
  try {
    const res = await fetch(`${API_BASE}/market/summary`);
    if (res.ok) {
      const data = await res.json();
      sectorMetrics = data.sector_metrics || [];
      sectorSelect.innerHTML = sectorMetrics
        .map((s) => `<option value="${s.sector}">${s.sector}</option>`)
        .join("");
    }
  } catch (err) {
    sectorSelect.innerHTML = `<option value="">Couldn't load sectors</option>`;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const experience = document.getElementById("rExperience").value;
    const reaction = document.getElementById("rReaction").value;
    const sectorName = sectorSelect.value;

    const tolerance = RISK_TOLERANCE[reaction];
    const sector = sectorMetrics.find((s) => s.sector === sectorName);

    if (!sector) {
      resultEl.className = "readiness-result show mismatch";
      resultEl.innerHTML = `<p class="result-title mismatch">Couldn't complete the check</p><p>Sector data isn't available right now — try again once the market data has loaded.</p>`;
      return;
    }

    const isMismatch = sector.avg_volatility_pct > tolerance.maxVolatility;

    if (isMismatch) {
      resultEl.className = "readiness-result show mismatch";
      resultEl.innerHTML = `
        <p class="result-title mismatch">Possible mismatch</p>
        <p>
          You described yourself as having a <strong>${tolerance.label.toLowerCase()}</strong> based on how you'd react to a sharp drop,
          but <strong>${sector.sector}</strong> has averaged <strong>${sector.avg_volatility_pct}%</strong> daily volatility in this dataset —
          higher than what someone with your stated reaction typically tolerates well.
        </p>
        <p>
          This is one of the most common patterns behind the "emotional control" and "market volatility difficulty" challenges reported in this study's survey:
          investors enter a sector without fully weighing how it matches their actual tolerance for swings, then react emotionally when the volatility they
          signed up for shows up.
        </p>
      `;
    } else {
      resultEl.className = "readiness-result show match";
      resultEl.innerHTML = `
        <p class="result-title match">Reasonable match</p>
        <p>
          Your stated risk tolerance (<strong>${tolerance.label.toLowerCase()}</strong>) is broadly in line with <strong>${sector.sector}</strong>'s
          average volatility (<strong>${sector.avg_volatility_pct}%</strong>) in this dataset. That doesn't remove the risk — it just means the swings
          you're likely to see are closer to what you've said you can sit through without panic-selling.
        </p>
      `;
    }
  });
}
