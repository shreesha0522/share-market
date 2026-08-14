"""
market.py — Market data loading and analysis for NEPSE historical price data.
"""

import os

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MARKET_DIR = os.path.join(PROJECT_ROOT, "data", "market")

SECTOR_MAP = {
    "NABIL": "Banking", "ADBL": "Banking", "SANIMA": "Banking",
    "NHPC": "Hydropower", "CHCL": "Hydropower", "UPPER": "Hydropower",
    "NLIC": "Insurance", "ALICL": "Insurance",
    "HIDCL": "Investment",
    "NTC": "Telecom",
}


def load_ticker(ticker, start=None, end=None):
    """Load one ticker's price history and compute volatility, drawdown, moving averages, and volume spikes."""
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
    """Load and concatenate all tickers' price histories for cross-company analysis."""
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
    """Compute 5-year return, volatility, and risk-adjusted return for each company."""
    cutoff = all_data["published_date"].max() - pd.DateOffset(years=recent_years)
    recent = all_data[all_data["published_date"] >= cutoff]

    metrics = []
    for ticker, group in recent.groupby("ticker"):
        group = group.sort_values("published_date")
        total_return = (group["close"].iloc[-1] / group["close"].iloc[0] - 1) * 100
        volatility = group["daily_return_pct"].std()
        avg_daily_volume = group["traded_quantity"].mean()
        risk_adjusted_return = None if volatility == 0 or pd.isna(volatility) else round(float(total_return / volatility), 2)

        metrics.append({
            "ticker": ticker,
            "sector": SECTOR_MAP[ticker],
            "start_price": round(float(group["close"].iloc[0]), 2),
            "latest_price": round(float(group["close"].iloc[-1]), 2),
            "total_return_pct": round(float(total_return), 2),
            "volatility_pct": round(float(volatility), 2),
            "avg_daily_volume": round(float(avg_daily_volume), 0),
            "n_trading_days": int(len(group)),
            "risk_adjusted_return": risk_adjusted_return,
        })
    return pd.DataFrame(metrics).sort_values("volatility_pct", ascending=False)


def compute_sector_metrics(company_metrics):
    """Aggregate company metrics up to sector-level averages, including risk-adjusted return."""
    result = (
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
    # Risk-adjusted return: average return per unit of average volatility.
    # Higher = better reward for the risk taken, not just higher raw return.
    result["risk_adjusted_return"] = (result["avg_return_pct"] / result["avg_volatility_pct"]).round(2)
    return result


def compute_extreme_days(df):
    """Return the 5 best and 5 worst single-day return days for a ticker's price history."""
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

    return {"best": to_day_list(best_days), "worst": to_day_list(worst_days)}


def compute_value_at_risk(df):
    """95% historical Value at Risk: the daily loss threshold exceeded only 5% of the time."""
    returns = df["Daily Return"].dropna()
    return None if returns.empty else round(float(returns.quantile(0.05)), 4)


def compute_correlation_matrix():
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
    return corr.where(pd.notna(corr), None)
