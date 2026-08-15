"""
Basic tests for the backend's core computation logic.
Run with: pytest tests/
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import market, survey


@pytest.fixture
def sample_price_df():
    """A small synthetic price series to test calculations against known values."""
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = pd.Series(100 + np.cumsum(np.random.RandomState(1).randn(60)))
    df = pd.DataFrame({
        "published_date": dates,
        "close": prices,
        "traded_quantity": np.random.RandomState(1).randint(1000, 5000, 60),
    })
    return df


def test_sector_map_has_all_tickers():
    """Every ticker should map to exactly one sector."""
    assert len(market.SECTOR_MAP) == 10
    assert all(isinstance(v, str) for v in market.SECTOR_MAP.values())


def test_challenge_labels_match_columns():
    """Every challenge column should have a corresponding human-readable label."""
    assert set(survey.CHALLENGE_COLS) == set(survey.CHALLENGE_LABELS.keys())


def test_experience_order_is_monotonic():
    """Experience levels should be ordered from least to most experienced."""
    values = list(survey.EXPERIENCE_ORDER.values())
    assert values == sorted(values)


def test_compute_company_metrics_shape(sample_price_df):
    """compute_company_metrics should return one row per ticker with expected columns."""
    sample_price_df["ticker"] = "NABIL"
    sample_price_df["sector"] = "Banking"
    sample_price_df["daily_return_pct"] = sample_price_df["close"].pct_change() * 100

    result = market.compute_company_metrics(sample_price_df, recent_years=5)

    assert len(result) == 1
    expected_cols = {
        "ticker", "sector", "start_price", "latest_price",
        "total_return_pct", "volatility_pct", "avg_daily_volume",
        "n_trading_days", "risk_adjusted_return",
    }
    assert expected_cols.issubset(set(result.columns))


def test_compute_sector_metrics_aggregates_correctly():
    """Sector metrics should average correctly across companies in the same sector."""
    company_metrics = pd.DataFrame([
        {"ticker": "A", "sector": "Banking", "total_return_pct": 10.0, "volatility_pct": 2.0},
        {"ticker": "B", "sector": "Banking", "total_return_pct": 20.0, "volatility_pct": 4.0},
    ])
    result = market.compute_sector_metrics(company_metrics)
    banking_row = result[result["sector"] == "Banking"].iloc[0]

    assert banking_row["avg_return_pct"] == 15.0
    assert banking_row["avg_volatility_pct"] == 3.0
    assert banking_row["n_companies"] == 2
    assert banking_row["risk_adjusted_return"] == 5.0  # 15.0 / 3.0


def test_compute_extreme_days_returns_five_each(sample_price_df):
    """compute_extreme_days should return exactly 5 best and 5 worst days."""
    sample_price_df["published_date"] = pd.to_datetime(sample_price_df["published_date"])
    sample_price_df = sample_price_df.set_index("published_date")
    sample_price_df = sample_price_df.rename(columns={"close": "Close"})
    sample_price_df["Daily Return"] = sample_price_df["Close"].pct_change()

    result = market.compute_extreme_days(sample_price_df)

    assert len(result["best"]) == 5
    assert len(result["worst"]) == 5
    assert result["best"][0]["return_pct"] >= result["best"][-1]["return_pct"]


def test_compute_value_at_risk_known_distribution():
    """VaR at 95% should equal the 5th percentile of a known set of returns."""
    df = pd.DataFrame({"Daily Return": [-0.10, -0.05, -0.02, 0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]})
    result = market.compute_value_at_risk(df)
    expected = df["Daily Return"].quantile(0.05)
    assert result == round(float(expected), 4)


def test_compute_value_at_risk_empty_returns_none():
    """VaR should return None rather than error when there's no return data."""
    df = pd.DataFrame({"Daily Return": [None, None]})
    result = market.compute_value_at_risk(df)
    assert result is None


def test_compute_sector_metrics_handles_zero_volatility():
    """Risk-adjusted return should be None (not a crash) when volatility is zero."""
    company_metrics = pd.DataFrame([
        {"ticker": "A", "sector": "Flat", "total_return_pct": 5.0, "volatility_pct": 0.0},
    ])
    result = market.compute_sector_metrics(company_metrics)
    flat_row = result[result["sector"] == "Flat"].iloc[0]
    assert pd.isna(flat_row["risk_adjusted_return"]) or flat_row["risk_adjusted_return"] is None
