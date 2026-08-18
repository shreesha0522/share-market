"""
ml.py — Machine learning models for the "New Investor Challenges — NEPSE" thesis project.

This complements the classical statistics in survey.py (OLS regression, Pearson
correlation) with supervised ML models trained on the same survey data:

1. A Random Forest regressor predicting a respondent's overall challenge score
   from their investing traits (experience, portfolio size, trade frequency,
   and average sector volatility exposure) — directly comparable to the OLS
   regression already reported in /api/survey/stats.
2. A Random Forest classifier predicting whether a respondent is "high challenge"
   (above the sample median) or "low challenge", plus which traits matter most
   (feature importance) — a different lens on the same question.
3. A live single-investor prediction: given one investor's traits, train both
   models on the FULL sample (no holdout) and predict their likely challenge
   score and high/low classification.

NOTE ON SECTOR COVERAGE: some respondents report investing in sectors not
tracked in the NEPSE market dataset (e.g. "Manufacturing", "Hotels", "Other").
For those respondents, exposure_volatility is imputed with the average
volatility across all tracked sectors, rather than dropping the respondent
entirely — this is a stated assumption, not a hidden one; the imputed count
is reported alongside every result so it can be disclosed in the write-up.

The evaluation models (1 and 2) train fresh on every call and hold out a test
split where sample size allows, since the goal there is an honest accuracy
figure to cite. The live prediction (3) intentionally trains on all available
data instead, since withholding data would only make a one-off estimate less
informed — it is not meant to produce a citable accuracy metric.
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
    plus each respondent's average exposure volatility (the market side of the study).
    Respondents invested only in sectors outside the tracked market dataset get their
    exposure volatility imputed with the overall tracked-sector average, flagged via
    'sector_outside_market_data', instead of being dropped from the analysis."""
    df = pd.read_csv(SURVEY_PATH)
    df["overall_challenge_score"] = df[CHALLENGE_COLS].mean(axis=1)

    df["experience_ordinal"] = df["years_investing"].map(EXPERIENCE_ORDER)
    df["portfolio_ordinal"] = df["portfolio_size"].map(PORTFOLIO_ORDER)
    df["trade_freq_ordinal"] = df["trade_frequency"].map(TRADE_FREQ_ORDER)

    sector_vol_lookup = sector_metrics.set_index("sector")["avg_volatility_pct"].to_dict()
    overall_mean_vol = float(np.mean(list(sector_vol_lookup.values())))

    def avg_exposure_volatility(sectors_str):
        sectors = [s.strip() for s in str(sectors_str).split(",")]
        vols = [sector_vol_lookup[s] for s in sectors if s in sector_vol_lookup]
        return np.mean(vols) if vols else np.nan

    df["exposure_volatility_raw"] = df["sectors_invested"].apply(avg_exposure_volatility)
    df["sector_outside_market_data"] = df["exposure_volatility_raw"].isna()
    df["exposure_volatility"] = df["exposure_volatility_raw"].fillna(overall_mean_vol)

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
        "n_imputed_sector_exposure": int(df["sector_outside_market_data"].sum()),
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
        "n_imputed_sector_exposure": int(df["sector_outside_market_data"].sum()),
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


def predict_for_investor(
    sector_metrics: pd.DataFrame,
    experience: str,
    portfolio: str,
    trade_freq: str,
    sector: str,
) -> dict[str, Any]:
    """
    Train both models on the FULL survey sample (no holdout — a single live prediction
    should use all available data rather than withhold some) and predict one investor's
    likely challenge score and high/low challenge classification from their stated traits.
    """
    if experience not in EXPERIENCE_ORDER:
        return {"error": f"Unknown experience bracket '{experience}'."}
    if portfolio not in PORTFOLIO_ORDER:
        return {"error": f"Unknown portfolio bracket '{portfolio}'."}
    if trade_freq not in TRADE_FREQ_ORDER:
        return {"error": f"Unknown trade frequency '{trade_freq}'."}

    sector_vol_lookup = sector_metrics.set_index("sector")["avg_volatility_pct"].to_dict()
    if sector not in sector_vol_lookup:
        return {"error": f"Unknown sector '{sector}'."}

    df = _build_features(sector_metrics)
    if len(df) < 5:
        return {"error": "Not enough survey data yet to make a prediction."}

    X_input = pd.DataFrame([{
        "experience_ordinal": EXPERIENCE_ORDER[experience],
        "portfolio_ordinal": PORTFOLIO_ORDER[portfolio],
        "trade_freq_ordinal": TRADE_FREQ_ORDER[trade_freq],
        "exposure_volatility": sector_vol_lookup[sector],
    }])[FEATURE_COLS]

    X, y = df[FEATURE_COLS], df["overall_challenge_score"]

    reg_model = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    reg_model.fit(X, y)
    predicted_score = float(reg_model.predict(X_input)[0])

    median_score = float(y.median())
    y_class = (y > median_score).astype(int)

    result: dict[str, Any] = {
        "predicted_challenge_score": round(predicted_score, 2),
        "sample_median_score": round(median_score, 2),
        "sample_average_score": round(float(y.mean()), 2),
        "n_training_samples": int(len(df)),
        "predicted_label": None,
        "confidence": None,
    }

    if y_class.nunique() >= 2:
        cls_model = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
        cls_model.fit(X, y_class)
        pred_class = int(cls_model.predict(X_input)[0])
        classes = list(cls_model.classes_)
        pred_proba = cls_model.predict_proba(X_input)[0]
        confidence = float(pred_proba[classes.index(1)]) if 1 in classes else None

        result["predicted_label"] = "high_challenge" if pred_class == 1 else "low_challenge"
        result["confidence"] = round(confidence, 3) if confidence is not None else None

    return result
