"""
Basic tests for the Flask backend's core computation logic.
Run with: pytest tests/
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as backend


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
    assert len(backend.SECTOR_MAP) == 10
    assert all(isinstance(v, str) for v in backend.SECTOR_MAP.values())


def test_challenge_labels_match_columns():
    """Every challenge column should have a corresponding human-readable label."""
    assert set(backend.CHALLENGE_COLS) == set(backend.CHALLENGE_LABELS.keys())


def test_experience_order_is_monotonic():
    """Experience levels should be ordered from least to most experienced."""
    values = list(backend.EXPERIENCE_ORDER.values())
    assert values == sorted(values)


def test_compute_company_metrics_shape(sample_price_df, tmp_path, monkeypatch):
    """compute_company_metrics should return one row per ticker with expected columns."""
    sample_price_df["ticker"] = "NABIL"
    sample_price_df["sector"] = "Banking"
    sample_price_df["daily_return_pct"] = sample_price_df["close"].pct_change() * 100

    result = backend.compute_company_metrics(sample_price_df, recent_years=5)

    assert len(result) == 1
    expected_cols = {
        "ticker", "sector", "start_price", "latest_price",
        "total_return_pct", "volatility_pct", "avg_daily_volume", "n_trading_days",
    }
    assert expected_cols.issubset(set(result.columns))


def test_compute_sector_metrics_aggregates_correctly():
    """Sector metrics should average correctly across companies in the same sector."""
    company_metrics = pd.DataFrame([
        {"ticker": "A", "sector": "Banking", "total_return_pct": 10.0, "volatility_pct": 2.0},
        {"ticker": "B", "sector": "Banking", "total_return_pct": 20.0, "volatility_pct": 4.0},
    ])
    result = backend.compute_sector_metrics(company_metrics)
    banking_row = result[result["sector"] == "Banking"].iloc[0]

    assert banking_row["avg_return_pct"] == 15.0
    assert banking_row["avg_volatility_pct"] == 3.0
    assert banking_row["n_companies"] == 2
