"""
survey.py — Survey data analysis: challenge scoring, demographic breakdowns, and statistics.
"""

import os

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SURVEY_PATH = os.path.join(PROJECT_ROOT, "data", "survey", "survey_synthetic.csv")

CHALLENGE_COLS = [
    "lacks_knowledge", "hard_to_access_info", "volatility_difficulty",
    "broker_platform_issues", "regulatory_confusion", "emotional_control",
    "limited_capital", "misled_by_rumors", "ipo_process_confusing", "lacks_mentorship",
]

CHALLENGE_LABELS = {
    "lacks_knowledge": "Lack of financial knowledge",
    "hard_to_access_info": "Hard to access reliable info",
    "volatility_difficulty": "Market volatility difficulty",
    "broker_platform_issues": "Broker/TMS platform issues",
    "regulatory_confusion": "Regulatory/tax confusion",
    "emotional_control": "Emotional control (fear/greed)",
    "limited_capital": "Limited capital",
    "misled_by_rumors": "Misled by rumors/tips",
    "ipo_process_confusing": "IPO/rights process confusion",
    "lacks_mentorship": "Lack of mentorship",
}

EXPERIENCE_ORDER = {"<1 year": 1, "1-3 years": 2, "3-5 years": 3, "5+ years": 4}
PORTFOLIO_ORDER = {
    "Below 50,000": 1, "50,000-200,000": 2, "200,000-500,000": 3,
    "500,000-1,000,000": 4, "Above 1,000,000": 5,
}
TRADE_FREQ_ORDER = {"Rarely": 1, "A few times a year": 2, "Monthly": 3, "Weekly": 4, "Daily": 5}


def analyze_survey():
    """Return ranked challenges, demographic breakdowns, and profitability/confidence stats."""
    df = pd.read_csv(SURVEY_PATH)

    overall_scores = df[CHALLENGE_COLS].mean().round(2)
    ranked = overall_scores.sort_values(ascending=False)
    ranked_named = [
        {"challenge": CHALLENGE_LABELS[k], "avg_score": float(v)}
        for k, v in ranked.items()
    ]

    df["overall_challenge_score"] = df[CHALLENGE_COLS].mean(axis=1)
    by_experience = (
        df.groupby("years_investing")["overall_challenge_score"]
        .mean()
        .round(2)
        .reindex(["<1 year", "1-3 years", "3-5 years", "5+ years"])
        .reset_index()
        .rename(columns={"years_investing": "experience", "overall_challenge_score": "avg_challenge_score"})
    )

    by_age = (
        df.groupby("age_group")["overall_challenge_score"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"age_group": "segment", "overall_challenge_score": "avg_challenge_score"})
    )

    profitability = df["profitable_experience"].value_counts(normalize=True).mul(100).round(1)
    confidence = df["confidence_change"].value_counts(normalize=True).mul(100).round(1)

    return {
        "n_respondents": int(len(df)),
        "ranked_challenges": ranked_named,
        "by_experience": by_experience.to_dict(orient="records"),
        "by_age": by_age.to_dict(orient="records"),
        "profitability_pct": profitability.to_dict(),
        "confidence_change_pct": confidence.to_dict(),
    }


def compute_sector_linkage(sector_metrics):
    """
    Links each sector's real market volatility to survey respondents'
    self-reported "market volatility difficulty" score for that sector —
    connecting the two halves of the study directly.
    """
    df = pd.read_csv(SURVEY_PATH)

    def respondent_sectors(sectors_str):
        return [s.strip() for s in str(sectors_str).split(",")]

    exploded = df.assign(sector=df["sectors_invested"].apply(respondent_sectors)).explode("sector")
    perceived = (
        exploded.groupby("sector")["volatility_difficulty"]
        .mean()
        .round(2)
        .rename("perceived_difficulty")
    )

    real_vol = sector_metrics.set_index("sector")["avg_volatility_pct"].rename("real_volatility_pct")

    linked = pd.concat([real_vol, perceived], axis=1).dropna().reset_index()
    linked = linked.rename(columns={"index": "sector"})

    return linked.to_dict(orient="records")


def statistical_analysis(sector_metrics):
    """Correlation and regression analysis linking investor traits to reported challenges."""
    import statsmodels.api as sm
    from scipy import stats

    df = pd.read_csv(SURVEY_PATH)
    df["overall_challenge_score"] = df[CHALLENGE_COLS].mean(axis=1)

    df["experience_ordinal"] = df["years_investing"].map(EXPERIENCE_ORDER)
    df["portfolio_ordinal"] = df["portfolio_size"].map(PORTFOLIO_ORDER)
    df["trade_freq_ordinal"] = df["trade_frequency"].map(TRADE_FREQ_ORDER)

    corr_exp, p_exp = stats.pearsonr(df["experience_ordinal"], df["overall_challenge_score"])
    corr_matrix = df[CHALLENGE_COLS].corr().round(2)

    sector_vol_lookup = sector_metrics.set_index("sector")["avg_volatility_pct"].to_dict()

    def avg_exposure_volatility(sectors_str):
        sectors = [s.strip() for s in str(sectors_str).split(",")]
        vols = [sector_vol_lookup[s] for s in sectors if s in sector_vol_lookup]
        return np.mean(vols) if vols else np.nan

    df["exposure_volatility"] = df["sectors_invested"].apply(avg_exposure_volatility)
    valid = df.dropna(subset=["exposure_volatility"])
    corr_vol, p_vol = stats.pearsonr(valid["exposure_volatility"], valid["volatility_difficulty"])

    X = df[["experience_ordinal", "portfolio_ordinal", "trade_freq_ordinal"]]
    X = sm.add_constant(X)
    y = df["overall_challenge_score"]
    model = sm.OLS(y, X).fit()

    regression_summary = {
        "r_squared": round(float(model.rsquared), 3),
        "coefficients": {
            name: {"coef": round(float(model.params[name]), 4), "p_value": round(float(model.pvalues[name]), 4)}
            for name in X.columns
        },
    }

    return {
        "experience_vs_challenge_correlation": {"r": round(float(corr_exp), 3), "p_value": round(float(p_exp), 4)},
        "volatility_vs_perceived_difficulty_correlation": {"r": round(float(corr_vol), 3), "p_value": round(float(p_vol), 4)},
        "challenge_item_correlation_matrix": corr_matrix.to_dict(),
        "regression": regression_summary,
    }
