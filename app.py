import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from io import BytesIO
from scipy.signal import argrelextrema

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="MASI Pro V4",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI Pro V4")

# =====================================================
# CACHE
# =====================================================

@st.cache_data
def load_data(file):

    df = pd.read_excel(
        file,
        sheet_name="Data_masi"
    )

    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Close"] = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    df = (
        df
        .dropna()
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


# =====================================================
# INDICATEURS
# =====================================================

def add_indicators(df):

    df["SMA20"] = ta.trend.sma_indicator(
        df["Close"],
        20
    )

    df["SMA50"] = ta.trend.sma_indicator(
        df["Close"],
        50
    )

    df["SMA200"] = ta.trend.sma_indicator(
        df["Close"],
        200
    )

    df["RSI"] = ta.momentum.rsi(
        df["Close"],
        14
    )

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["SIGNAL"] = (
        macd.macd_signal()
    )

    df["HISTO"] = (
        df["MACD"]
        - df["SIGNAL"]
    )

    bb = ta.volatility.BollingerBands(
        df["Close"],
        20,
        2
    )

    df["BB_UP"] = (
        bb.bollinger_hband()
    )

    df["BB_LOW"] = (
        bb.bollinger_lband()
    )

    df["RET"] = np.log(
        df["Close"]
        / df["Close"].shift(1)
    )

    df["VOL20"] = (
        df["RET"]
        .rolling(20)
        .std()
        * np.sqrt(252)
    )

    return df


# =====================================================
# SUPPORTS
# =====================================================

def detect_sr(df):

    prices = df["Close"].values

    mins = argrelextrema(
        prices,
        np.less,
        order=5
    )[0]

    maxs = argrelextrema(
        prices,
        np.greater,
        order=5
    )[0]

    supports = prices[mins]
    resistances = prices[maxs]

    return supports, resistances


# =====================================================
# SCORE
# =====================================================

def compute_score(df):

    last = df.iloc[-1]

    score = 0
    comments = []

    if last["Close"] > last["SMA200"]:
        score += 20
        comments.append(
            "✅ Cours > SMA200"
        )

    if last["SMA50"] > last["SMA200"]:
        score += 15
        comments.append(
            "✅ SMA50 > SMA200"
        )

    if last["SMA20"] > last["SMA50"]:
        score += 10
        comments.append(
            "✅ SMA20 > SMA50"
        )

    if last["MACD"] > last["SIGNAL"]:
        score += 15
        comments.append(
            "✅ MACD haussier"
        )

    if 45 <= last["RSI"] <= 65:
        score += 15

    if last["VOL20"] < 0.20:
        score += 10

    golden = (
        last["SMA50"]
        > last["SMA200"]
    )

    if golden:
        score += 10

    return score, comments


# =====================================================
# BACKTEST
# =====================================================

def run_backtest(df):

    buy = (
        (df["SMA20"] > df["SMA50"])
        &
        (df["MACD"] > df["SIGNAL"])
        &
        (df["RSI"] > 50)
    )

    sell = (
        (df["SMA20"] < df["SMA50"])
        |
        (df["MACD"] < df["SIGNAL"])
        |
        (df["RSI"] < 45)
    )

    position = 0
    entry = 0

    trades = []

    for i in range(len(df)):

        price = df["Close"].iloc[i]

        if position == 0 and buy.ilocposition = 1
            entry = price

        elif position == 1 and sell.ilocperf = (
                (price - entry)
                / entry
            ) * 100

            trades.append(perf)

            position = 0

    return trades


# =====================================================
# LOAD FILE
# =====================================================

uploaded = st.file_uploader(
    "Importer Excel",
    type=["xlsx"]
)

if uploaded:

    df = load_data(uploaded)

    df = add_indicators(df)

    df = df.dropna()

    score, comments = compute_score(df)

    supports, resistances = detect_sr(df)

    # KPIs

    st.header("🎯 Analyse")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Cours",
        round(
            df["Close"].iloc[-1],
            2
        )
    )

    c2.metric(
        "RSI",
        round(
            df["RSI"].iloc[-1],
            2
        )
    )

    c3.metric(
        "Score",
        score
    )

    for x in comments:
        st.write(x)

    # Graphique

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            name="Close"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA20"],
            name="SMA20"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA50"],
            name="SMA50"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA200"],
            name="SMA200"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["BB_UP"],
            name="BB_UP"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["BB_LOW"],
            name="BB_LOW"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Backtest

    st.header("📊 Backtest")

    trades = run_backtest(df)

    if len(trades):

        winrate = (
            np.mean(
                np.array(trades) > 0
            ) * 100
        )

        perf = sum(trades)

        b1, b2 = st.columns(2)

        b1.metric(
            "Win Rate",
            f"{winrate:.1f}%"
        )

        b2.metric(
            "Performance",
            f"{perf:.2f}%"
        )

    # Export

    buffer = BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="MASI",
            index=False
        )

    st.download_button(
        "📥 Télécharger",
        buffer.getvalue(),
        "MASI_PRO_V4.xlsx"
    )
