"""
app.py — Flask backend for the "New Investor Challenges — NEPSE" thesis project.
Exposes market + survey analysis (same logic as your original scripts/analysis.py)
as a JSON API for the HTML/CSS/JS frontend to consume.
"""

import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET_DIR = os.path.join(PROJECT_ROOT, "data", "market")
SURVEY_PATH = os.path.join(PROJECT_ROOT, "data", "survey", "survey_synthetic.csv")

SECTOR_MAP = {
    "NABIL": "Banking", "ADBL": "Banking", "SANIMA": "Banking",
    "NHPC": "Hydropower", "CHCL": "Hydropower", "UPPER": "Hydropower",
    "NLIC": "Insurance", "ALICL": "Insurance",
    "HIDCL": "Investment",
    "NTC": "Telecom",
}

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


def load_ticker(ticker, start=None, end=None):
    path = os.path.join(MARKET_DIR, f"{ticker}.csv")
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    df = df.dropna(subset=["published_date", "close"])
    df = df.sort_values("published_date")
    df = df.set_index("published_date")
    df = df.rename(columns={"close": "Close", "traded_quantity": "Volume"})

    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    df["Daily Return"] = df["Close"].pct_change()
    df["Volatility_30d"] = df["Daily Return"].rolling(30).std()
    df["Running_Max"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - df["Running_Max"]) / df["Running_Max"]
    df["MA_20"] = df["Close"].rolling(20).mean()
    df["MA_50"] = df["Close"].rolling(50).mean()
    df["Volume_MA_20"] = df["Volume"].rolling(20).mean()
    df["Volume_Spike"] = df["Volume"] > (2 * df["Volume_MA_20"])

    return df


def load_market_data_all():
    frames = []
    for ticker, sector in SECTOR_MAP.items():
        path = os.path.join(MARKET_DIR, f"{ticker}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
        df = df.dropna(subset=["published_date", "close"])
        df = df.sort_values("published_date")
        df["ticker"] = ticker
        df["sector"] = sector
        df["daily_return_pct"] = df["close"].pct_change() * 100
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def compute_company_metrics(all_data, recent_years=5):
    cutoff = all_data["published_date"].max() - pd.DateOffset(years=recent_years)
    recent = all_data[all_data["published_date"] >= cutoff]

    metrics = []
    for ticker, group in recent.groupby("ticker"):
        group = group.sort_values("published_date")
        total_return = (group["close"].iloc[-1] / group["close"].iloc[0] - 1) * 100
        volatility = group["daily_return_pct"].std()
        avg_daily_volume = group["traded_quantity"].mean()
        metrics.append({
            "ticker": ticker,
            "sector": SECTOR_MAP[ticker],
            "start_price": round(float(group["close"].iloc[0]), 2),
            "latest_price": round(float(group["close"].iloc[-1]), 2),
            "total_return_pct": round(float(total_return), 2),
            "volatility_pct": round(float(volatility), 2),
            "avg_daily_volume": round(float(avg_daily_volume), 0),
            "n_trading_days": int(len(group)),
        })
    return pd.DataFrame(metrics).sort_values("volatility_pct", ascending=False)


def compute_sector_metrics(company_metrics):
    return (
        company_metrics.groupby("sector")
        .agg(
            avg_return_pct=("total_return_pct", "mean"),
            avg_volatility_pct=("volatility_pct", "mean"),
            n_companies=("ticker", "count"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_volatility_pct", ascending=False)
    )


def analyze_survey():
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


def statistical_analysis(sector_metrics):
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


@app.route("/api/tickers")
def api_tickers():
    return jsonify([{"ticker": t, "sector": s} for t, s in SECTOR_MAP.items()])


@app.route("/api/market/<ticker>")
def api_market_ticker(ticker):
    ticker = ticker.upper()
    if ticker not in SECTOR_MAP:
        return jsonify({"error": f"Unknown ticker '{ticker}'"}), 404

    start = request.args.get("start")
    end = request.args.get("end")

    for label, value in (("start", start), ("end", end)):
        if value:
            try:
                pd.to_datetime(value)
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid '{label}' date format. Use YYYY-MM-DD."}), 400

    df = load_ticker(ticker, start, end)

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

    returns = df["Daily Return"].dropna()
    var_95 = None if returns.empty else round(float(returns.quantile(0.05)), 4)

    returns_with_dates = df["Daily Return"].dropna()
    best_days = returns_with_dates.nlargest(5)
    worst_days = returns_with_dates.nsmallest(5)

    def to_day_list(series):
        return [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "return_pct": round(float(val) * 100, 2),
                "close": round(float(df.loc[idx, "Close"]), 2),
            }
            for idx, val in series.items()
        ]

    extreme_days = {
        "best": to_day_list(best_days),
        "worst": to_day_list(worst_days),
    }

    summary = {
        "ticker": ticker,
        "sector": SECTOR_MAP[ticker],
        "avg_volatility": None if df["Volatility_30d"].dropna().empty else round(float(df["Volatility_30d"].mean()), 4),
        "max_drawdown": None if df["Drawdown"].dropna().empty else round(float(df["Drawdown"].min()), 4),
        "volume_spike_days": int(df["Volume_Spike"].sum()),
        "latest_close": round(float(df["Close"].iloc[-1]), 2),
        "var_95": var_95,
    }

    return jsonify({"summary": summary, "series": series, "extreme_days": extreme_days})


@app.route("/api/market/summary")
def api_market_summary():
    all_data = load_market_data_all()
    company_metrics = compute_company_metrics(all_data)
    sector_metrics = compute_sector_metrics(company_metrics)
    return jsonify({
        "company_metrics": company_metrics.to_dict(orient="records"),
        "sector_metrics": sector_metrics.to_dict(orient="records"),
    })


@app.route("/api/market/correlation")
def api_market_correlation():
    """
    Correlation matrix of daily returns across all companies.
    Shows whether holding multiple stocks actually diversifies risk —
    highly correlated stocks move together and offer little real diversification.
    """
    frames = {}
    for ticker in SECTOR_MAP:
        path = os.path.join(MARKET_DIR, f"{ticker}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
        df = df.dropna(subset=["published_date", "close"]).sort_values("published_date")
        df = df.set_index("published_date")
        df = df[~df.index.duplicated(keep="first")]  # some NEPSE CSVs have duplicate dates
        frames[ticker] = df["close"].pct_change()

    combined = pd.DataFrame(frames)
    corr = combined.corr().round(2)
    corr = corr.where(pd.notna(corr), None)

    return jsonify({
        "tickers": list(corr.columns),
        "matrix": corr.to_dict(),
    })


@app.route("/api/survey/summary")
def api_survey_summary():
    """Return ranked challenges, demographic breakdowns, and profitability stats from the survey."""
    if not os.path.exists(SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    result = analyze_survey()
    result["is_synthetic"] = True
    return jsonify(result)


@app.route("/api/survey/stats")
def api_survey_stats():
    """Return correlation and regression analysis linking investor traits to reported challenges."""
    if not os.path.exists(SURVEY_PATH):
        return jsonify({"error": "Survey data not found"}), 404
    all_data = load_market_data_all()
    company_metrics = compute_company_metrics(all_data)
    sector_metrics = compute_sector_metrics(company_metrics)
    result = statistical_analysis(sector_metrics)
    return jsonify(result)


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
    app.run(debug=True, port=5000)
