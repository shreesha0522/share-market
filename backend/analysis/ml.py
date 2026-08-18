"""
ml.py — Machine learning models for the "New Investor Challenges — NEPSE" thesis project.

This complements the classical statistics in survey.py (OLS regression, Pearson
correlation) with two supervised ML models trained on the same survey data:

1. A Random Forest regressor predicting a respondent's overall challenge score
   from their investing traits (experience, portfolio size, trade frequency,
   and average sector volatility exposure) — directly comparable to the OLS
   regression already reported in /api/survey/stats.
2. A Random Forest classifier predicting whether a respondent is "high challenge"
   (above the sample median) or "low challenge", plus which traits matter most
   (feature importance) — a different lens on the same question.

Both models train fresh on every call. The survey dataset for a thesis project
is small (tens to a few hundred rows), so this is not meant to be a production
model — it's meant to produce an honest, reproducible R²/accuracy figure you
can cite, with a held-out test set where the sample size allows one.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from analysis.survey import (
    CHALLENGE_COLS,
    EXPERIENCE_ORDER,
    PORTFOLIO_ORDER,
    SURVEY_PATH,
    TRADE_FREQ_ORDER,
)

FEATURE_COLS = ["experience_ordinal", "portfolio_ordinal", "trade_freq_ordinal", "exposure_volatility"]

RANDOM_STATE = 42  # fixed seed so results are reproducible for the write-up
MIN_ROWS_FOR_HOLDOUT = 12  # below this, a train/test split is too noisy to mean anything


def _build_features(sector_metrics: pd.DataFrame) -> pd.DataFrame:
    """Load survey data and engineer the same features used in survey.statistical_analysis,
    plus each respondent's average exposure volatility (the market side of the study)."""
    df = pd.read_csv(SURVEY_PATH)
    df["overall_challenge_score"] = df[CHALLENGE_COLS].mean(axis=1)

    df["experience_ordinal"] = df["years_investing"].map(EXPERIENCE_ORDER)
    df["portfolio_ordinal"] = df["portfolio_size"].map(PORTFOLIO_ORDER)
    df["trade_freq_ordinal"] = df["trade_frequency"].map(TRADE_FREQ_ORDER)

    sector_vol_lookup = sector_metrics.set_index("sector")["avg_volatility_pct"].to_dict()

    def avg_exposure_volatility(sectors_str):
        sectors = [s.strip() for s in str(sectors_str).split(",")]
        vols = [sector_vol_lookup[s] for s in sectors if s in sector_vol_lookup]
        return np.mean(vols) if vols else np.nan

    df["exposure_volatility"] = df["sectors_invested"].apply(avg_exposure_volatility)
    return df.dropna(subset=FEATURE_COLS + ["overall_challenge_score"])


def _safe_split(X, y, stratify=None):
    """Train/test split that degrades gracefully on small survey samples: below
    MIN_ROWS_FOR_HOLDOUT rows, train on everything and flag that no real holdout
    was used, instead of returning a test-set metric that isn't meaningful."""
    if len(X) < MIN_ROWS_FOR_HOLDOUT:
        return X, X, y, y, False
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=stratify
    )
    return X_train, X_test, y_train, y_test, True


def predict_challenge_score(sector_metrics: pd.DataFrame) -> dict[str, Any]:
    """Random Forest regression predicting overall challenge score from investor traits,
    reported alongside a plain linear regression baseline for comparison."""
    df = _build_features(sector_metrics)
    X, y = df[FEATURE_COLS], df["overall_challenge_score"]
    X_train, X_test, y_train, y_test, had_holdout = _safe_split(X, y)

    model = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    baseline = LinearRegression().fit(X_train, y_train)
    baseline_preds = baseline.predict(X_test)

    return {
        "n_samples": int(len(df)),
        "used_holdout_test_set": had_holdout,
        "test_set_size": int(len(X_test)),
        "random_forest": {
            "r_squared": round(float(r2_score(y_test, preds)), 3),
            "mae": round(float(mean_absolute_error(y_test, preds)), 3),
            "feature_importance": {k: round(float(v), 4) for k, v in zip(FEATURE_COLS, model.feature_importances_)},
        },
        "linear_regression_baseline": {
            "r_squared": round(float(r2_score(y_test, baseline_preds)), 3),
            "mae": round(float(mean_absolute_error(y_test, baseline_preds)), 3),
        },
    }


def classify_high_challenge(sector_metrics: pd.DataFrame) -> dict[str, Any]:
    """Random Forest classifier: is a respondent 'high challenge' (above the sample
    median overall score) or 'low challenge', predicted from the same investor traits."""
    df = _build_features(sector_metrics)
    median_score = df["overall_challenge_score"].median()
    df["high_challenge"] = (df["overall_challenge_score"] > median_score).astype(int)

    X, y = df[FEATURE_COLS], df["high_challenge"]
    if y.nunique() < 2:
        return {"error": "Not enough variation in challenge scores to classify — all respondents fall on one side of the median."}

    stratify = y if len(df) >= MIN_ROWS_FOR_HOLDOUT else None
    X_train, X_test, y_train, y_test, had_holdout = _safe_split(X, y, stratify=stratify)

    model = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    return {
        "n_samples": int(len(df)),
        "median_challenge_score": round(float(median_score), 2),
        "used_holdout_test_set": had_holdout,
        "test_set_size": int(len(X_test)),
        "accuracy": round(float(accuracy_score(y_test, preds)), 3),
        "precision": round(float(precision_score(y_test, preds, zero_division=0)), 3),
        "recall": round(float(recall_score(y_test, preds, zero_division=0)), 3),
        "f1": round(float(f1_score(y_test, preds, zero_division=0)), 3),
        "confusion_matrix": {
            "labels": ["low_challenge", "high_challenge"],
            "matrix": confusion_matrix(y_test, preds, labels=[0, 1]).tolist(),
        },
        "feature_importance": {k: round(float(v), 4) for k, v in zip(FEATURE_COLS, model.feature_importances_)},
    }
