"""
Tests for analysis/ml.py — the Random Forest regression, classification, and
live single-investor prediction models.

These use a synthetic survey CSV (monkeypatched over ml.SURVEY_PATH) rather
than the real survey data, so the tests are stable regardless of how many
real responses have been collected.

Run with: pytest tests/
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::sklearn.exceptions.UndefinedMetricWarning")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import ml
from analysis.survey import CHALLENGE_COLS


@pytest.fixture
def sector_metrics():
    """Synthetic sector volatility table, matching the shape of market.compute_sector_metrics output."""
    return pd.DataFrame([
        {"sector": "Banking", "avg_volatility_pct": 1.5},
        {"sector": "Hydropower", "avg_volatility_pct": 2.5},
        {"sector": "Insurance", "avg_volatility_pct": 2.0},
        {"sector": "Investment", "avg_volatility_pct": 2.8},
        {"sector": "Telecom", "avg_volatility_pct": 1.8},
    ])


def _make_survey_df(n, sectors, rng_seed=0):
    """Build a synthetic survey dataframe with n rows and varied challenge scores,
    so classification has both high and low challenge respondents."""
    rng = np.random.RandomState(rng_seed)
    experiences = ["<1 year", "1-3 years", "3-5 years", "5+ years"]
    portfolios = ["Below 50,000", "50,000-200,000", "200,000-500,000", "500,000-1,000,000", "Above 1,000,000"]
    trade_freqs = ["Rarely", "A few times a year", "Monthly", "Weekly", "Daily"]

    rows = []
    for i in range(n):
        row = {
            "years_investing": experiences[i % len(experiences)],
            "portfolio_size": portfolios[i % len(portfolios)],
            "trade_frequency": trade_freqs[i % len(trade_freqs)],
            "sectors_invested": sectors[i % len(sectors)],
        }
        # Alternate high/low challenge scores so there's real variation to classify.
        base = 4.5 if i % 2 == 0 else 1.5
        for col in CHALLENGE_COLS:
            row[col] = min(5, max(1, base + rng.uniform(-0.5, 0.5)))
        rows.append(row)
    return pd.DataFrame(rows)


@pytest.fixture
def patch_survey(monkeypatch, tmp_path):
    """Writes a given survey dataframe to a temp CSV and points ml.SURVEY_PATH at it."""
    def _patch(df):
        path = tmp_path / "survey.csv"
        df.to_csv(path, index=False)
        monkeypatch.setattr(ml, "SURVEY_PATH", str(path))
        return path
    return _patch


def test_choose_k_scales_with_sample_size():
    """Fold count should grow with more data but stay within [2, 5]."""
    assert ml._choose_k(8) == 2
    assert ml._choose_k(20) == 5
    assert ml._choose_k(100) == 5
    assert ml._choose_k(0) == 2  # never below the floor, even for degenerate input


def test_build_features_imputes_out_of_scope_sectors(sector_metrics, patch_survey):
    """A respondent investing only in a sector outside the tracked market data
    should be imputed with the average volatility, not dropped."""
    df = _make_survey_df(3, sectors=["Banking", "Manufacturing", "Hydropower"])
    patch_survey(df)

    result = ml._build_features(sector_metrics)

    assert len(result) == 3  # nobody dropped
    flagged = result[result["sectors_invested"] == "Manufacturing"]
    assert len(flagged) == 1
    assert flagged.iloc[0]["sector_outside_market_data"] == True
    expected_mean_vol = sector_metrics["avg_volatility_pct"].mean()
    assert flagged.iloc[0]["exposure_volatility"] == pytest.approx(expected_mean_vol)


def test_predict_challenge_score_too_few_rows_returns_error(sector_metrics, patch_survey):
    """Below MIN_ROWS_FOR_CV, the regressor should report an error instead of a misleading metric."""
    df = _make_survey_df(4, sectors=["Banking"])
    patch_survey(df)

    result = ml.predict_challenge_score(sector_metrics)

    assert "error" in result
    assert result["n_samples"] == 4


def test_predict_challenge_score_shape(sector_metrics, patch_survey):
    """With enough rows, the regressor should return cross-validated metrics for both models."""
    df = _make_survey_df(16, sectors=["Banking", "Hydropower", "Insurance"])
    patch_survey(df)

    result = ml.predict_challenge_score(sector_metrics)

    assert result["n_samples"] == 16
    assert result["cv_folds"] == ml._choose_k(16)
    assert "r_squared_mean" in result["random_forest"]
    assert "r_squared_std" in result["random_forest"]
    assert "mae_mean" in result["random_forest"]
    assert set(result["random_forest"]["feature_importance"].keys()) == set(ml.FEATURE_COLS)
    assert "r_squared_mean" in result["linear_regression_baseline"]


def test_classify_high_challenge_shape(sector_metrics, patch_survey):
    """With varied challenge scores and enough rows, the classifier should return
    cross-validated accuracy/F1 and a confusion matrix built from out-of-fold predictions."""
    df = _make_survey_df(16, sectors=["Banking", "Hydropower", "Insurance"])
    patch_survey(df)

    result = ml.classify_high_challenge(sector_metrics)

    assert result["n_samples"] == 16
    assert 0.0 <= result["accuracy_mean"] <= 1.0
    assert result["confusion_matrix"]["labels"] == ["low_challenge", "high_challenge"]
    matrix = result["confusion_matrix"]["matrix"]
    total_predictions = sum(sum(row) for row in matrix)
    assert total_predictions == 16  # every respondent appears exactly once across folds


def test_classify_high_challenge_no_variation_returns_error(sector_metrics, patch_survey):
    """If every respondent has an identical challenge score, there's no median split to classify."""
    df = _make_survey_df(10, sectors=["Banking"])
    for col in CHALLENGE_COLS:
        df[col] = 3.0  # force identical scores, wiping out the alternating high/low pattern
    patch_survey(df)

    result = ml.classify_high_challenge(sector_metrics)

    assert "error" in result


def test_predict_for_investor_rejects_unknown_category(sector_metrics, patch_survey):
    """An invalid category value (typo, wrong casing) should return a clear error, not crash."""
    df = _make_survey_df(10, sectors=["Banking"])
    patch_survey(df)

    result = ml.predict_for_investor(sector_metrics, "not a real bracket", "50,000-200,000", "Monthly", "Banking")

    assert "error" in result


def test_predict_for_investor_rejects_unknown_sector(sector_metrics, patch_survey):
    """A sector not in the market dataset should return a clear error, not crash."""
    df = _make_survey_df(10, sectors=["Banking"])
    patch_survey(df)

    result = ml.predict_for_investor(sector_metrics, "1-3 years", "50,000-200,000", "Monthly", "NotASector")

    assert "error" in result


def test_predict_for_investor_returns_a_prediction(sector_metrics, patch_survey):
    """With valid inputs and enough training data, a live prediction should come back complete."""
    df = _make_survey_df(10, sectors=["Banking", "Hydropower"])
    patch_survey(df)

    result = ml.predict_for_investor(sector_metrics, "1-3 years", "50,000-200,000", "Monthly", "Banking")

    assert "error" not in result
    assert isinstance(result["predicted_challenge_score"], float)
    assert 1.0 <= result["predicted_challenge_score"] <= 5.0
    assert result["n_training_samples"] == 10
    assert result["predicted_label"] in ("high_challenge", "low_challenge")
    assert 0.0 <= result["confidence"] <= 1.0
