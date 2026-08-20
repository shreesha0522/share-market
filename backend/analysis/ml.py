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
   models on the FULL sample and predict their likely challenge score and
   high/low classification.

EVALUATION METHOD: with only ~18 survey respondents, a single train/test split
is noisy — whichever few rows land in the test set can swing R²/accuracy
wildly and unrepresentatively. Models 1 and 2 below use K-FOLD CROSS-VALIDATION
instead: the data is split into K folds, each fold takes a turn as the test
set while the model trains on the rest, and the metrics reported are the
mean ± standard deviation across all folds. This is a materially more honest
estimate of how well the model generalizes than one split, and is what should
be cited in the thesis write-up. K is chosen automatically based on sample
size (see _choose_k below) and always reported alongside the results.

NOTE ON SECTOR COVERAGE: some respondents report investing in sectors not
tracked in the NEPSE market dataset (e.g. "Manufacturing", "Hotels", "Other").
For those respondents, exposure_volatility is imputed with the average
volatility across all tracked sectors, rather than dropping the respondent
entirely — this is a stated assumption, not a hidden one; the imputed count
is reported alongside every result so it can be disclosed in the write-up.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
)

from analysis.survey import (
    CHALLENGE_COLS,
    EXPERIENCE_ORDER,
    PORTFOLIO_ORDER,
    SURVEY_PATH,
    TRADE_FREQ_ORDER,
)

FEATURE_COLS = ["experience_ordinal", "portfolio_ordinal", "trade_freq_ordinal", "exposure_volatility"]

RANDOM_STATE = 42  # fixed seed so results are reproducible for the write-up
MIN_ROWS_FOR_CV = 8  # below this, even cross-validation folds are too small to be meaningful


def _choose_k(n_rows: int) -> int:
    """Pick a fold count that keeps at least ~4 rows per test fold, capped at 5."""
    return max(2, min(5, n_rows // 4))


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


def predict_challenge_score(sector_metrics: pd.DataFrame) -> dict[str, Any]:
    """Random Forest regression predicting overall challenge score from investor traits,
    evaluated with K-fold cross-validation (mean ± std R²/MAE across folds), reported
    alongside a plain linear regression baseline evaluated the same way."""
    df = _build_features(sector_metrics)
    X, y = df[FEATURE_COLS], df["overall_challenge_score"]
    n = len(df)

    if n < MIN_ROWS_FOR_CV:
        return {
            "error": f"Only {n} usable survey responses — need at least {MIN_ROWS_FOR_CV} for cross-validated evaluation.",
            "n_samples": n,
        }

    k = _choose_k(n)
    kf = KFold(n_splits=k, shuffle=True, random_state=RANDOM_STATE)

    rf = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    rf_r2_folds = cross_val_score(rf, X, y, cv=kf, scoring="r2")
    rf_mae_folds = -cross_val_score(rf, X, y, cv=kf, scoring="neg_mean_absolute_error")

    lin = LinearRegression()
    lin_r2_folds = cross_val_score(lin, X, y, cv=kf, scoring="r2")
    lin_mae_folds = -cross_val_score(lin, X, y, cv=kf, scoring="neg_mean_absolute_error")

    # Fit on the full sample once more to report feature importance (not fold-specific,
    # but the standard way to report importance when the fit itself is cross-validated).
    rf_full = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=RANDOM_STATE).fit(X, y)

    return {
        "n_samples": n,
        "n_imputed_sector_exposure": int(df["sector_outside_market_data"].sum()),
        "cv_folds": k,
        "random_forest": {
            "r_squared_mean": round(float(rf_r2_folds.mean()), 3),
            "r_squared_std": round(float(rf_r2_folds.std()), 3),
            "mae_mean": round(float(rf_mae_folds.mean()), 3),
            "mae_std": round(float(rf_mae_folds.std()), 3),
            "feature_importance": {k_: round(float(v), 4) for k_, v in zip(FEATURE_COLS, rf_full.feature_importances_)},
        },
        "linear_regression_baseline": {
            "r_squared_mean": round(float(lin_r2_folds.mean()), 3),
            "r_squared_std": round(float(lin_r2_folds.std()), 3),
            "mae_mean": round(float(lin_mae_folds.mean()), 3),
            "mae_std": round(float(lin_mae_folds.std()), 3),
        },
    }


def classify_high_challenge(sector_metrics: pd.DataFrame) -> dict[str, Any]:
    """Random Forest classifier: is a respondent 'high challenge' (above the sample
    median overall score) or 'low challenge', evaluated with stratified K-fold
    cross-validation (mean ± std accuracy/F1 across folds)."""
    df = _build_features(sector_metrics)
    median_score = df["overall_challenge_score"].median()
    df["high_challenge"] = (df["overall_challenge_score"] > median_score).astype(int)

    X, y = df[FEATURE_COLS], df["high_challenge"]
    n = len(df)

    if y.nunique() < 2:
        return {"error": "Not enough variation in challenge scores to classify — all respondents fall on one side of the median."}
    if n < MIN_ROWS_FOR_CV:
        return {
            "error": f"Only {n} usable survey responses — need at least {MIN_ROWS_FOR_CV} for cross-validated evaluation.",
            "n_samples": n,
        }

    k = _choose_k(n)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=RANDOM_STATE)

    model = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    acc_folds = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    f1_folds = cross_val_score(model, X, y, cv=skf, scoring="f1", error_score=np.nan)
    precision_folds = cross_val_score(model, X, y, cv=skf, scoring="precision", error_score=np.nan)
    recall_folds = cross_val_score(model, X, y, cv=skf, scoring="recall", error_score=np.nan)

    # Out-of-fold predictions give an honest confusion matrix without a second holdout.
    oof_preds = cross_val_predict(model, X, y, cv=skf)

    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y, oof_preds, labels=[0, 1]).tolist()

    model_full = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=RANDOM_STATE).fit(X, y)

    return {
        "n_samples": n,
        "n_imputed_sector_exposure": int(df["sector_outside_market_data"].sum()),
        "median_challenge_score": round(float(median_score), 2),
        "cv_folds": k,
        "accuracy_mean": round(float(np.nanmean(acc_folds)), 3),
        "accuracy_std": round(float(np.nanstd(acc_folds)), 3),
        "precision_mean": round(float(np.nanmean(precision_folds)), 3),
        "recall_mean": round(float(np.nanmean(recall_folds)), 3),
        "f1_mean": round(float(np.nanmean(f1_folds)), 3),
        "f1_std": round(float(np.nanstd(f1_folds)), 3),
        "confusion_matrix": {
            "labels": ["low_challenge", "high_challenge"],
            "matrix": cm,
            "note": "Built from out-of-fold predictions across all cross-validation folds, not a separate holdout.",
        },
        "feature_importance": {k_: round(float(v), 4) for k_, v in zip(FEATURE_COLS, model_full.feature_importances_)},
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
        "n_training_samples": len(df),
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
