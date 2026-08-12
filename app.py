import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="New Investor Market Risk Dashboard — NEPSE",
    page_icon="📊",
    layout="wide"
)

# ---- Where the real NEPSE CSVs live ----
# This file expects: <project_root>/data/market/<TICKER>.csv
# (app.py sits directly in the project root, so we look in ./data/market)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "market")

SECTOR_MAP = {
    "NABIL": "Banking", "ADBL": "Banking", "SANIMA": "Banking",
    "NHPC": "Hydropower", "CHCL": "Hydropower", "UPPER": "Hydropower",
    "NLIC": "Insurance", "ALICL": "Insurance",
    "HIDCL": "Investment",
    "NTC": "Telecom",
}

# ---- Sidebar controls ----
with st.sidebar:
    st.header("⚙️ Controls")
    tickers = st.multiselect(
        "Choose NEPSE companies to compare",
        options=list(SECTOR_MAP.keys()),
        default=["NABIL", "NHPC", "NLIC"],
        format_func=lambda t: f"{t} ({SECTOR_MAP[t]})"
    )
    start_date = st.date_input("Start date", value=pd.to_datetime("2021-01-01"))
    end_date = st.date_input("End date", value=pd.to_datetime("2026-07-01"))
    st.markdown("---")
    st.caption("Built for a Bachelor's thesis on challenges faced by new investors in the Nepal share market (NEPSE).")

# ---- Header ----
st.title("📊 New Investor Market Risk Dashboard — NEPSE")
st.markdown(
    "Explore **volatility** and **drawdown risk** across NEPSE-listed companies — the kind of risk "
    "new investors often misjudge before it's too late."
)

if not tickers:
    st.info("👈 Pick at least one company from the sidebar to begin.")
    st.stop()


# ---- Data loading (real NEPSE data, not yfinance) ----
@st.cache_data
def load_data(ticker, start, end):
    path = os.path.join(DATA_DIR, f"{ticker}.csv")
    df = pd.read_csv(path)
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    df = df.dropna(subset=["published_date", "close"])
    df = df.sort_values("published_date")
    df = df.set_index("published_date")
    df = df.rename(columns={"close": "Close", "traded_quantity": "Volume"})

    # filter to selected date range
    df = df[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]

    df["Daily Return"] = df["Close"].pct_change()
    df["Volatility_30d"] = df["Daily Return"].rolling(30).std()
    df["Running_Max"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - df["Running_Max"]) / df["Running_Max"]
    df["MA_20"] = df["Close"].rolling(20).mean()
    df["MA_50"] = df["Close"].rolling(50).mean()

    # volume spike detector (crowd behavior / FOMO indicator), carried over from your notebook
    df["Volume_MA_20"] = df["Volume"].rolling(20).mean()
    df["Volume_Spike"] = df["Volume"] > (2 * df["Volume_MA_20"])

    return df


all_data = {t: load_data(t, start_date, end_date) for t in tickers}

# guard against empty data (e.g. date range outside what's available)
empty_tickers = [t for t, df in all_data.items() if df.empty]
if empty_tickers:
    st.warning(f"No data available for {', '.join(empty_tickers)} in the selected date range. Try a wider range.")
    tickers = [t for t in tickers if t not in empty_tickers]
if not tickers:
    st.stop()

# ---- Summary metric cards ----
st.subheader("Quick Summary")
cols = st.columns(len(tickers))
for col, t in zip(cols, tickers):
    avg_vol = all_data[t]["Volatility_30d"].mean()
    max_dd = all_data[t]["Drawdown"].min()
    spikes = int(all_data[t]["Volume_Spike"].sum())
    col.metric(label=f"{t} — Avg Volatility", value=f"{avg_vol:.3f}")
    col.metric(label=f"{t} — Max Drawdown", value=f"{max_dd:.1%}")
    col.metric(label=f"{t} — Volume Spike Days", value=spikes)

st.markdown("---")

# ---- Tabs for each analysis ----
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Volatility", "📉 Drawdown", "📊 Trend (Moving Avg)", "🔊 Volume Spikes", "🧾 Data Table"
])

with tab1:
    st.markdown("**Volatility** measures how much a stock's price swings day to day. Higher volatility = harder for new investors to judge risk.")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for t in tickers:
        ax.plot(all_data[t].index, all_data[t]["Volatility_30d"], label=f"{t} ({SECTOR_MAP[t]})")
    ax.set_xlabel("Date")
    ax.set_ylabel("30-day Volatility")
    ax.legend()
    st.pyplot(fig)

with tab2:
    st.markdown("**Drawdown** shows how far a stock has fallen from its most recent peak — this is what actually scares new investors into panic-selling.")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for t in tickers:
        ax.plot(all_data[t].index, all_data[t]["Drawdown"], label=f"{t} ({SECTOR_MAP[t]})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.legend()
    st.pyplot(fig)

with tab3:
    st.markdown("**Moving averages** help distinguish a real trend from short-term noise — something new investors often struggle to do.")
    selected = st.selectbox("Choose one company to view trend detail:", tickers)
    df = all_data[selected]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df.index, df["Close"], label="Close Price", alpha=0.4)
    ax.plot(df.index, df["MA_20"], label="20-day MA")
    ax.plot(df.index, df["MA_50"], label="50-day MA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (NPR)")
    ax.set_title(f"{selected} ({SECTOR_MAP[selected]}) — Price with Moving Averages")
    ax.legend()
    st.pyplot(fig)

with tab4:
    st.markdown(
        "**Volume spikes** (days where trading volume exceeds 2x its 20-day average) often signal "
        "crowd behavior — FOMO buying or panic selling — exactly the kind of pattern new investors "
        "get caught up in without realizing it."
    )
    selected_v = st.selectbox("Choose one company:", tickers, key="volume_select")
    dfv = all_data[selected_v]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(dfv.index, dfv["Volume"], color="steelblue", alpha=0.5, label="Daily Volume")
    spike_days = dfv[dfv["Volume_Spike"]]
    ax.scatter(spike_days.index, spike_days["Volume"], color="red", s=20, label="Spike Day", zorder=5)
    ax.set_xlabel("Date")
    ax.set_ylabel("Traded Quantity")
    ax.set_title(f"{selected_v} — Volume with Spike Days Highlighted")
    ax.legend()
    st.pyplot(fig)
    st.caption(f"Total spike days in range: {int(dfv['Volume_Spike'].sum())} out of {len(dfv)} trading days")

with tab5:
    summary = pd.DataFrame({
        t: {
            "Sector": SECTOR_MAP[t],
            "Avg Volatility": all_data[t]["Volatility_30d"].mean(),
            "Max Drawdown": all_data[t]["Drawdown"].min(),
            "Latest Close (NPR)": all_data[t]["Close"].iloc[-1],
            "Volume Spike Days": int(all_data[t]["Volume_Spike"].sum()),
        }
        for t in tickers
    }).T
    st.dataframe(
        summary.style.format({
            "Avg Volatility": "{:.3f}",
            "Max Drawdown": "{:.1%}",
            "Latest Close (NPR)": "Rs. {:.2f}",
        })
    )
