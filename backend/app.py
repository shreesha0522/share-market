"""
app.py — Flask backend for the "New Investor Challenges — NEPSE" thesis project.
This file only defines API routes; all analysis logic lives in analysis/market.py,
analysis/survey.py, and analysis/ml.py.
"""

import os

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from analysis import market, ml, survey

load_dotenv()  # loads variables from a .env file if present, falls back to defaults below

app = Flask(__name__)
CORS(app)

FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"


@app.route("/api/tickers")
def api_tickers():
    return jsonify([{"ticker": t, "sector": s} for t, s in market.SECTOR_MAP.items()])


@app.route("/api/market/<ticker>")
def api_market_ticker(ticker):
    ticker = ticker.upper()
    if ticker not in market.SECTOR_MAP:
        return jsonify({"error": f"Unknown ticker '{ticker}'"}), 404

    start = request.args.get("start")
    end = request.args.get("end")

    for label, value in (("start", start), ("end", end)):
        if value:
            try:
                pd.to_datetime(value)
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid '{label}' date format. Use YYYY-MM-DD."}), 400

    df = market.load_ticker(ticker, start, end)

    if df is None:
        return jsonify({"error": f"No data file found for '{ticker}'"}), 404
    if df.empty:
        return jsonify({"error": "No data in the selected date range"}), 404

    series = {
        "dates": df.index.strftime("%Y-%m-%d").tolist(),
        "close": df["Close"].round(2).tolist(),
        "volume": df["Volume"].fillna(0).tolist(),
        "volatility_30d": df["Volatility_30d"].round(4).astype(object).where(pd.notna(df["Volatility_30d"]), None).tolist(),
        "drawdown": df["Drawdown"].round(4).astype(object).where(pd.notna(df["Drawdown"]), None).tolist(),
        "ma_20": df["MA_20"].round(2).astype(object).where(pd.notna(df["MA_20"]), None).tolist(),
        "ma_50": df["MA_50"].round(2).astype(object).where(pd.notna(df["MA_50"]), None).tolist(),
        "volume_spike": df["Volume_Spike"].fillna(False).tolist(),
    }

    summary = {
        "ticker": ticker,
        "sector": market.SECTOR_MAP[ticker],
        "avg_volatility": None if df["Volatility_30d"].dropna().empty else round(float(df["Volatility_30d"].mean()), 4),
        "max_drawdown": None if df["Drawdown"].dropna().empty else round(float(df["Drawdown"].min()), 4),
        "volume_spike_days": int(df["Volume_Spike"].sum()),
        "latest_close": round(float(df["Close"].iloc[-1]), 2),
        "var_95": market.compute_value_at_risk(df),
    }

    return jsonify({
        "summary": summary,
        "series": series,
        "extreme_days": market.compute_extreme_days(df),
    })


@app.route("/api/market/summary")
def api_market_summary():
    all_data = market.load_market_data_all()
    company_metrics = market.compute_company_metrics(all_data)
    sector_metrics = market.compute_sector_metrics(company_metrics)
    return jsonify({
        "company_metrics": company_metrics.to_dict(orient="records"),
        "sector_metrics": sector_metrics.to_dict(orient="records"),
    })


@app.route("/api/market/correlation")
def api_market_correlation():
    corr = market.compute_correlation_matrix()
    return jsonify({
        "tickers": list(corr.columns),
        "matrix": corr.to_dict(),
    })

@app.route("/api/survey/summary")
def api_survey_summary():
    """Return ranked challenges, demographic breakdowns, and profitability stats from the survey."""
    if not os.path.exists(survey.SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    result = survey.analyze_survey()
    result["is_synthetic"] = survey.is_synthetic_data()
    return jsonify(result)


@app.route("/api/survey/stats")
def api_survey_stats():
    """Return correlation and regression analysis linking investor traits to reported challenges."""
    if not os.path.exists(survey.SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    all_data = market.load_market_data_all()
    company_metrics = market.compute_company_metrics(all_data)
    sector_metrics = market.compute_sector_metrics(company_metrics)
    result = survey.statistical_analysis(sector_metrics)
    return jsonify(result)


@app.route("/api/survey/linkage")
def api_survey_linkage():
    """Links each sector's real market volatility to survey respondents' perceived difficulty for it."""
    if not os.path.exists(survey.SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    all_data = market.load_market_data_all()
    company_metrics = market.compute_company_metrics(all_data)
    sector_metrics = market.compute_sector_metrics(company_metrics)
    linkage = survey.compute_sector_linkage(sector_metrics)
    return jsonify({"linkage": linkage, "is_synthetic": survey.is_synthetic_data()})


@app.route("/api/survey/ml")
def api_survey_ml():
    """
    Machine learning models predicting investor challenge outcomes from investing traits.
    Complements the classical OLS regression in /api/survey/stats with:
      - a Random Forest regressor predicting overall challenge score (vs a linear baseline)
      - a Random Forest classifier separating "high challenge" from "low challenge" respondents
    """
    if not os.path.exists(survey.SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    all_data = market.load_market_data_all()
    company_metrics = market.compute_company_metrics(all_data)
    sector_metrics = market.compute_sector_metrics(company_metrics)
    return jsonify({
        "is_synthetic": survey.is_synthetic_data(),
        "challenge_score_prediction": ml.predict_challenge_score(sector_metrics),
        "high_challenge_classification": ml.classify_high_challenge(sector_metrics),
    })


@app.route("/api/health")
def api_health():
    """Simple liveness check for the API."""
    return jsonify({"status": "ok"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
