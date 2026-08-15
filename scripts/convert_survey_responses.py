"""
convert_survey_responses.py — Converts a raw Google Forms CSV export into the
clean schema the analysis pipeline expects (matching survey_synthetic.csv).

Usage:
    python3 scripts/convert_survey_responses.py path/to/raw_export.csv

Outputs: data/survey/survey_real.csv
"""

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(PROJECT_ROOT, "data", "survey", "survey_real.csv")

LIKERT_MAP = {
    "Strongly disagree": 1,
    "Stronger disagree": 1,  # typo present in the live form (Q16/Q17/Q21)
    "Strongly diagree": 1,   # typo present in the live form (Q21)
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly agree": 5,
}

# Raw form headers -> clean column names
COLUMN_MAP = {
    "Q1. Have you invested in the Nepal Stock Exchange (NEPSE)?": "invested_in_nepse",
    "Q2. How long have you been investing?": "years_investing",
    "Q3. Age group": "age_group",
    "Q4. Gender": "gender",
    "Q5. Education level": "education",
    "Q6. Occupation": "occupation",
    "Q7. Monthly income (NPR)": "monthly_income",
    "Q8. Approximate portfolio size (NPR)": "portfolio_size",
    "Q9. How often do you trade?": "trade_frequency",
    "Q10. Which sectors do you invest in?": "sectors_invested",
    "Q11. Main source of investment information": "info_source",
    "Q12. I lack sufficient knowledge about fundamental/technical analysis": "lacks_knowledge",
    "Q13. I find it hard to access reliable, timely market information": "hard_to_access_info",
    "Q14. Market volatility makes it difficult to plan my investments": "volatility_difficulty",
    "Q15. I have faced issues with my broker/TMS platform (technical glitches, delays)": "broker_platform_issues",
    "Q16. I don't fully understand regulatory/tax procedures related to investing": "regulatory_confusion",
    "Q17: I struggle to control my emotions (fear, greed, panic) when trading": "emotional_control",
    "Q18: I have limited capital, which restricts my investment options": "limited_capital",
    "Q19: I have been misled by rumors or unreliable tips": "misled_by_rumors",
    "Q20: I find IPO/rights share allotment processes confusing": "ipo_process_confusing",
    "Q21: I lack access to mentorship or expert guidance": "lacks_mentorship",
    "Q22. What is the single biggest challenge you've faced as a new investor?": "biggest_challenge_text",
    "Q23. What would have helped you the most when you started investing?": "what_would_help_text",
    "Q24. Overall, has your investment experience been profitable so far?": "profitable_experience",
    "Q25.How would you rate your confidence in making investment decisions now vs. when you started?": "confidence_change",
}

CHALLENGE_COLS = [
    "lacks_knowledge", "hard_to_access_info", "volatility_difficulty",
    "broker_platform_issues", "regulatory_confusion", "emotional_control",
    "limited_capital", "misled_by_rumors", "ipo_process_confusing", "lacks_mentorship",
]

# Normalize en-dashes (–) to hyphens (-) used by the analysis code's lookup dicts
DASH_FIX_COLUMNS = ["years_investing", "age_group", "monthly_income", "portfolio_size"]


def normalize_dashes(value):
    if isinstance(value, str):
        return value.replace("–", "-")
    return value


def convert(raw_path):
    df = pd.read_csv(raw_path)
    df = df.rename(columns=COLUMN_MAP)

    n_total = len(df)

    # Exclude respondents who said they have not actually invested in NEPSE —
    # this study is about the experience of active investors.
    if "invested_in_nepse" in df.columns:
        excluded = (df["invested_in_nepse"] != "Yes").sum()
        df = df[df["invested_in_nepse"] == "Yes"].copy()
        df = df.drop(columns=["invested_in_nepse"])
    else:
        excluded = 0

    # Fix "Less than 1 year" -> "<1 year" to match EXPERIENCE_ORDER keys
    if "years_investing" in df.columns:
        df["years_investing"] = df["years_investing"].replace({"Less than 1 year": "<1 year"})

    for col in DASH_FIX_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(normalize_dashes)

    # Likert text -> 1-5 integers
    for col in CHALLENGE_COLS:
        if col in df.columns:
            df[col] = df[col].map(LIKERT_MAP)

    # profitable_experience: form offers Yes/No/Maybe; code expects
    # Yes/No/Break-even/Not sure. "Maybe" is mapped to "Not sure" as the
    # closest equivalent — there is no direct "Break-even" option in the
    # live form, so that category will not appear in real data.
    if "profitable_experience" in df.columns:
        df["profitable_experience"] = df["profitable_experience"].replace({"Maybe": "Not sure"})

    df.insert(0, "response_id", range(1, len(df) + 1))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Converted {len(df)} of {n_total} responses ({excluded} excluded: did not invest in NEPSE).")
    print(f"Written to {OUT_PATH}")

    missing_likert = [
        (col, df[col].isna().sum()) for col in CHALLENGE_COLS if col in df.columns and df[col].isna().sum() > 0
    ]
    if missing_likert:
        print("\nWARNING: unmapped Likert values found (check for new typos in form text):")
        for col, n in missing_likert:
            print(f"  {col}: {n} unmapped")

    return df


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/convert_survey_responses.py path/to/raw_export.csv")
        sys.exit(1)
    convert(sys.argv[1])
