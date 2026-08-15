"""
validate_data.py — Checks the NEPSE market CSVs and survey CSV for common
data quality issues before they're used in analysis: missing values,
duplicate dates, and out-of-range prices.

Run with: python3 scripts/validate_data.py
"""

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET_DIR = os.path.join(PROJECT_ROOT, "data", "market")
SURVEY_PATH = os.path.join(PROJECT_ROOT, "data", "survey", "survey_synthetic.csv")

TICKERS = ["NABIL", "ADBL", "SANIMA", "NHPC", "CHCL", "UPPER", "NLIC", "ALICL", "HIDCL", "NTC"]


def validate_market_csv(ticker):
    path = os.path.join(MARKET_DIR, f"{ticker}.csv")
    issues = []

    if not os.path.exists(path):
        return [f"File not found: {path}"]

    df = pd.read_csv(path)

    if "published_date" not in df.columns or "close" not in df.columns:
        issues.append("Missing required columns (published_date, close)")
        return issues

    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")

    n_bad_dates = df["published_date"].isna().sum()
    if n_bad_dates > 0:
        issues.append(f"{n_bad_dates} rows with unparseable dates")

    n_missing_close = df["close"].isna().sum()
    if n_missing_close > 0:
        issues.append(f"{n_missing_close} rows with missing close price")

    n_duplicate_dates = df["published_date"].duplicated().sum()
    if n_duplicate_dates > 0:
        issues.append(f"{n_duplicate_dates} duplicate dates (handled by dropping duplicates in analysis code)")

    n_negative_close = (df["close"] < 0).sum()
    if n_negative_close > 0:
        issues.append(f"{n_negative_close} rows with negative close price")

    return issues


def validate_survey_csv():
    issues = []
    if not os.path.exists(SURVEY_PATH):
        return [f"File not found: {SURVEY_PATH}"]

    df = pd.read_csv(SURVEY_PATH)
    n_rows = len(df)

    if n_rows == 0:
        issues.append("Survey file is empty")
        return issues

    challenge_cols = [c for c in df.columns if c.startswith(("lacks_", "hard_", "volatility_", "broker_",
                                                                "regulatory_", "emotional_", "limited_",
                                                                "misled_", "ipo_"))]
    for col in challenge_cols:
        out_of_range = ((df[col] < 1) | (df[col] > 5)).sum()
        if out_of_range > 0:
            issues.append(f"{out_of_range} out-of-range values (expected 1-5) in '{col}'")

    return issues


def main():
    print("=" * 60)
    print("DATA QUALITY VALIDATION")
    print("=" * 60)

    any_issues = False

    print("\nMarket data:")
    for ticker in TICKERS:
        issues = validate_market_csv(ticker)
        if issues:
            any_issues = True
            print(f"  {ticker}: {len(issues)} issue(s)")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  {ticker}: OK")

    print("\nSurvey data:")
    issues = validate_survey_csv()
    if issues:
        any_issues = True
        print(f"  survey_synthetic.csv: {len(issues)} issue(s)")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  survey_synthetic.csv: OK")

    print("\n" + "=" * 60)
    if any_issues:
        print("Some issues found — review above. Duplicate dates are already")
        print("handled defensively in the analysis code (first occurrence kept).")
    else:
        print("All data passed validation checks.")
    print("=" * 60)

    return 1 if any_issues else 0


if __name__ == "__main__":
    sys.exit(main())
