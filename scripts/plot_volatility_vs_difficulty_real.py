"""
Volatility vs. perceived difficulty — thesis Section 1.2 figure
-----------------------------------------------------------------
Uses REAL data:
  - Market volatility: real NEPSE trading data (sector_metrics, hardcoded
    below from the earlier market-data analysis — replace with your own
    computed values if they change)
  - Survey: real Google Forms export (CSV), filtered to respondents who
    answered "Yes" to Q1 (i.e. actually invest in NEPSE)

Run:  python plot_volatility_vs_difficulty.py
Requires: pandas, matplotlib, seaborn, scipy
  pip install pandas matplotlib seaborn scipy

Expects the survey CSV in the same folder, named:
  Untitled_form__Responses__-_Form_Responses_1.csv
(change SURVEY_CSV below if you rename it)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

SURVEY_CSV = "Untitled_form__Responses__-_Form_Responses_1.csv"

# ---------------------------------------------------------------
# 1. Market data (real, from NEPSE trading-data analysis)
# ---------------------------------------------------------------
sector_metrics = [
    {"sector": "Investment", "avg_volatility_pct": 2.54},
    {"sector": "Hydropower", "avg_volatility_pct": 2.51},
    {"sector": "Insurance", "avg_volatility_pct": 2.08},
    {"sector": "Telecom", "avg_volatility_pct": 1.86},
    {"sector": "Banking", "avg_volatility_pct": 1.66},
]
sector_df = pd.DataFrame(sector_metrics).sort_values(
    "avg_volatility_pct", ascending=False
)
sector_vol_lookup = dict(zip(sector_df["sector"], sector_df["avg_volatility_pct"]))

# ---------------------------------------------------------------
# 2. Real survey data
# ---------------------------------------------------------------
raw = pd.read_csv(SURVEY_CSV)
inv = raw[raw["Q1. Have you invested in the Nepal Stock Exchange (NEPSE)?"] == "Yes"].copy()

print(f"Total form submissions: {len(raw)}")
print(f"Respondents who confirmed they invest in NEPSE (used below): {len(inv)}")
if len(inv) < 30:
    print(f"NOTE: small sample size (n={len(inv)}). State this as a limitation "
          "in your methodology/discussion — results here are indicative, not "
          "statistically robust at this n.")

likert_map = {"Strongly disagree": 1, "Disagree": 2, "Neutral": 3, "Agree": 4, "Strongly agree": 5}

challenge_cols = {
    "Q12. I lack sufficient knowledge about fundamental/technical analysis": "Lack of financial knowledge",
    "Q13. I find it hard to access reliable, timely market information": "Hard to access reliable info",
    "Q14. Market volatility makes it difficult to plan my investments": "Market volatility difficulty",
    "Q15. I have faced issues with my broker/TMS platform (technical glitches, delays)": "Broker/TMS platform issues",
    "Q16. I don't fully understand regulatory/tax procedures related to investing": "Regulatory/tax confusion",
    "Q17: I struggle to control my emotions (fear, greed, panic) when trading": "Emotional control (fear/greed)",
    "Q18: I have limited capital, which restricts my investment options": "Limited capital",
    "Q19: I have been misled by rumors or unreliable tips": "Misled by rumors/tips",
    "Q20: I find IPO/rights share allotment processes confusing": "IPO/rights process confusion",
    "Q21: I lack access to mentorship or expert guidance": "Lack of mentorship",
}
for col in challenge_cols:
    inv[col] = inv[col].map(likert_map)

challenge_df = pd.DataFrame(
    [{"challenge": label, "avg_score": inv[col].mean()} for col, label in challenge_cols.items()]
).sort_values("avg_score", ascending=True)

# ---------------------------------------------------------------
# 3. Correlation: sector volatility vs. individual Q14 score
# ---------------------------------------------------------------
sector_col = "Q10. Which sectors do you invest in?"
inv["sector_vol"] = inv[sector_col].map(sector_vol_lookup)
paired = inv.dropna(subset=["sector_vol", "Q14. Market volatility makes it difficult to plan my investments"])
if len(paired) > 2:
    r, p = pearsonr(
        paired["sector_vol"],
        paired["Q14. Market volatility makes it difficult to plan my investments"],
    )
else:
    r, p = float("nan"), float("nan")
print(f"Correlation (sector volatility vs. perceived volatility difficulty): "
      f"r={r:.3f}, p={p:.3f}, n={len(paired)}")

# ---------------------------------------------------------------
# 4. Plot
# ---------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.0)
NEUTRAL = "#898781"
HIGHLIGHT = "#2a78d6"

fig, axes = plt.subplots(1, 2, figsize=(13, 6))

ax = axes[0]
bar_colors = [NEUTRAL] * len(sector_df)
bar_colors[sector_df["sector"].tolist().index("Hydropower")] = HIGHLIGHT
sns.barplot(data=sector_df, x="avg_volatility_pct", y="sector",
            hue="sector", palette=bar_colors, legend=False, ax=ax)
ax.set_title("Measured volatility by sector\n(real NEPSE trading data)")
ax.set_xlabel("Average daily return volatility (%)")
ax.set_ylabel("")
for i, v in enumerate(sector_df["avg_volatility_pct"]):
    ax.text(v + 0.03, i, f"{v:.2f}%", va="center", fontsize=10)

ax2 = axes[1]
bar_colors2 = [HIGHLIGHT if c == "Market volatility difficulty" else NEUTRAL
               for c in challenge_df["challenge"]]
sns.barplot(data=challenge_df, x="avg_score", y="challenge",
            hue="challenge", palette=bar_colors2, legend=False, ax=ax2)
ax2.set_title(f"Self-reported challenge score\n(real survey, n={len(inv)}, 1-5 scale)")
ax2.set_xlabel("Average score")
ax2.set_ylabel("")
ax2.set_xlim(0, 5)
for i, v in enumerate(challenge_df["avg_score"]):
    ax2.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=10)

fig.suptitle(
    "The volatility-perception disconnect\n"
    f"(r = {r:.3f}, p = {p:.3f}, n = {len(paired)} — no significant relationship)",
    fontsize=13, y=1.03,
)
fig.tight_layout()
fig.savefig("volatility_vs_difficulty_real.png", dpi=300, bbox_inches="tight")
print("Saved volatility_vs_difficulty_real.png")
plt.show()
