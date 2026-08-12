"""
generate_synthetic_survey.py

*** SYNTHETIC / DUMMY DATA ONLY ***
Generates FAKE survey responses matching the real survey structure, so the
pipeline can be built/tested before real Google Forms responses arrive.
Replace data/survey/survey_synthetic.csv with real exported data later.
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)
N = 220

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(PROJECT_ROOT, "data", "survey", "survey_synthetic.csv")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
age_p = [0.35, 0.30, 0.18, 0.11, 0.06]

education = ["High school", "Bachelor's", "Master's", "PhD", "Other"]
edu_p = [0.15, 0.55, 0.25, 0.03, 0.02]

occupation = ["Student", "Salaried employee", "Business owner", "Self-employed", "Unemployed", "Other"]
occ_p = [0.30, 0.40, 0.15, 0.10, 0.03, 0.02]

income = ["Below 25,000", "25,000-50,000", "50,000-100,000", "Above 100,000", "Prefer not to say"]
income_p = [0.20, 0.30, 0.30, 0.15, 0.05]

experience = ["<1 year", "1-3 years", "3-5 years", "5+ years"]
experience_p = [0.35, 0.30, 0.20, 0.15]

portfolio = ["Below 50,000", "50,000-200,000", "200,000-500,000", "500,000-1,000,000", "Above 1,000,000"]
portfolio_p = [0.30, 0.35, 0.20, 0.10, 0.05]

trade_freq = ["Daily", "Weekly", "Monthly", "A few times a year", "Rarely"]
trade_p = [0.10, 0.25, 0.30, 0.25, 0.10]

sectors_list = ["Banking", "Hydropower", "Insurance", "Hotels", "Manufacturing", "Microfinance"]
info_sources = ["TMS/broker app", "Financial news", "Social media", "Friends & family", "Financial advisor", "ShareSansar/MeroLagani"]

challenge_cols = [
    "lacks_knowledge", "hard_to_access_info", "volatility_difficulty",
    "broker_platform_issues", "regulatory_confusion", "emotional_control",
    "limited_capital", "misled_by_rumors", "ipo_process_confusing", "lacks_mentorship",
]

rows = []
for i in range(N):
    exp = np.random.choice(experience, p=experience_p)
    base_challenge = 4.0 if exp in ["<1 year", "1-3 years"] else 2.8

    row = {
        "response_id": i + 1,
        "age_group": np.random.choice(age_groups, p=age_p),
        "gender": np.random.choice(["Male", "Female", "Prefer not to say", "Other"], p=[0.62, 0.34, 0.03, 0.01]),
        "education": np.random.choice(education, p=edu_p),
        "occupation": np.random.choice(occupation, p=occ_p),
        "monthly_income": np.random.choice(income, p=income_p),
        "years_investing": exp,
        "portfolio_size": np.random.choice(portfolio, p=portfolio_p),
        "trade_frequency": np.random.choice(trade_freq, p=trade_p),
        "sectors_invested": ", ".join(np.random.choice(sectors_list, size=np.random.randint(1, 4), replace=False)),
        "info_source": np.random.choice(info_sources),
    }

    for col in challenge_cols:
        score = np.clip(np.random.normal(base_challenge, 0.9), 1, 5)
        row[col] = round(score)

    row["profitable_experience"] = np.random.choice(["Yes", "No", "Break-even", "Not sure"], p=[0.30, 0.30, 0.25, 0.15])
    row["confidence_change"] = np.random.choice(
        ["Much lower", "Lower", "Same", "Higher", "Much higher"], p=[0.05, 0.15, 0.25, 0.35, 0.20]
    )
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUT_PATH, index=False)
print(f"Generated {len(df)} synthetic survey responses at {OUT_PATH}")
