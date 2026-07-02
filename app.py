import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="New Investor Market Risk Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---- Sidebar controls ----
with st.sidebar:
    st.header("⚙️ Controls")
    tickers = st.multiselect(
        "Choose stocks to compare",
        ["AAPL", "TSLA", "JNJ", "MSFT", "NVDA", "KO"],
        default=["AAPL", "TSLA", "JNJ"]
    )
    start_date = st.date_input("Start date", value=pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End date", value=pd.to_datetime("2026-01-01"))
    st.markdown("---")
    st.caption("Built for a Bachelor's thesis on challenges faced by new investors in the share market.")

# ---- Header ----
st.title("📊 New Investor Market Risk Dashboard")
st.markdown(
    "Explore **volatility** and **drawdown risk** across stocks — the kind of risk "
    "new investors often misjudge before it's too late."
)

if not tickers:
    st.info("👈 Pick at least one stock from the sidebar to begin.")
    st.stop()

# ---- Data loading ----
@st.cache_data
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df.columns = df.columns.get_level_values(0)
    df["Daily Return"] = df["Close"].pct_change()
    df["Volatility_30d"] = df["Daily Return"].rolling(30).std()
    df["Running_Max"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - df["Running_Max"]) / df["Running_Max"]
    df["MA_20"] = df["Close"].rolling(20).mean()
    df["MA_50"] = df["Close"].rolling(50).mean()
    return df

all_data = {t: load_data(t, start_date, end_date) for t in tickers}

# ---- Summary metric cards ----
st.subheader("Quick Summary")
cols = st.columns(len(tickers))
for col, t in zip(cols, tickers):
    avg_vol = all_data[t]["Volatility_30d"].mean()
    max_dd = all_data[t]["Drawdown"].min()
    col.metric(label=f"{t} — Avg Volatility", value=f"{avg_vol:.3f}")
    col.metric(label=f"{t} — Max Drawdown", value=f"{max_dd:.1%}")

st.markdown("---")

# ---- Tabs for each analysis ----
tab1, tab2, tab3, tab4 = st.tabs(["📈 Volatility", "📉 Drawdown", "📊 Trend (Moving Avg)", "🧾 Data Table"])

with tab1:
    st.markdown("**Volatility** measures how much a stock's price swings day to day. Higher volatility = harder for new investors to judge risk.")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for t in tickers:
        ax.plot(all_data[t]["Volatility_30d"], label=t)
    ax.set_xlabel("Date")
    ax.set_ylabel("Volatility")
    ax.legend()
    st.pyplot(fig)

with tab2:
    st.markdown("**Drawdown** shows how far a stock has fallen from its most recent peak — this is what actually scares new investors into panic-selling.")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for t in tickers:
        ax.plot(all_data[t]["Drawdown"], label=t)
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.legend()
    st.pyplot(fig)

with tab3:
    st.markdown("**Moving averages** help distinguish a real trend from short-term noise — something new investors often struggle to do.")
    selected = st.selectbox("Choose one stock to view trend detail:", tickers)
    df = all_data[selected]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df["Close"], label="Close Price", alpha=0.4)
    ax.plot(df["MA_20"], label="20-day MA")
    ax.plot(df["MA_50"], label="50-day MA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    st.pyplot(fig)

with tab4:
    summary = pd.DataFrame({
        t: {
            "Avg Volatility": all_data[t]["Volatility_30d"].mean(),
            "Max Drawdown": all_data[t]["Drawdown"].min(),
            "Latest Close": all_data[t]["Close"].iloc[-1],
        }
        for t in tickers
    }).T
    st.dataframe(summary.style.format({"Avg Volatility": "{:.3f}", "Max Drawdown": "{:.1%}", "Latest Close": "${:.2f}"}))