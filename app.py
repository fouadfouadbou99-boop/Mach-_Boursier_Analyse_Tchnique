import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from io import BytesIO
from scipy.signal import argrelextrema

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="MASI Pro V4",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI Pro V4")

# =====================================================
# CHARGEMENT
# =====================================================

@st.cache_data
def load_data(file):

    df = pd.read_excel(
        file,
        sheet_name="Data_masi",
        engine="openpyxl"
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
        .dropna(subset=["Date", "Close"])
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
        window=20
    )

    df["SMA50"] = ta.trend.sma_indicator(
        df["Close"],
        window=50
    )

    df["SMA200"] = ta.trend.sma_indicator(
        df["Close"],
        window=200
    )

    df["RSI"] = ta.momentum.rsi(
        df["Close"],
        window=14
    )

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["SIGNAL"] = macd.macd_signal()

    df["HISTO"] = (
        df["MACD"]
        - df["SIGNAL"]
    )

    bb = ta.volatility.BollingerBands(
        close=df["Close"],
        window=20,
        window_dev=2
    )

    df["BB_UP"] = bb.bollinger_hband()
    df["BB_LOW"] = bb.bollinger_lband()

    return df


# =====================================================
# SUPPORTS / RESISTANCES
# =====================================================

def detect_sr(df):

    prices = df["Close"].values

    minima = argrelextrema(
        prices,
        np.less,
        order=5
    )[0]

    maxima = argrelextrema(
        prices,
        np.greater,
        order=5
    )[0]

    supports = prices[minima]
    resistances = prices[maxima]

    return supports, resistances


# =====================================================
# SCORE
# =====================================================

def calculate_score(df):

    score = 0

    last = df.iloc[-1]

    if last["Close"] > last["SMA200"]:
        score += 25

    if last["SMA50"] > last["SMA200"]:
        score += 25

    if last["SMA20"] > last["SMA50"]:
        score += 20

    if last["MACD"] > last["SIGNAL"]:
        score += 15

    if 45 <= last["RSI"] <= 70:
        score += 15

    return min(score, 100)


# =====================================================
# APPLICATION
# =====================================================

uploaded_file = st.file_uploader(
    "Importer Data_masi.xlsx",
    type=["xlsx"]
)

if uploaded_file:

    try:

        df = load_data(uploaded_file)

        df = add_indicators(df)

        df = df.dropna()

        score = calculate_score(df)

        supports, resistances = detect_sr(df)

        last = df.iloc[-1]

        st.header("🎯 Résumé")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Cours",
            round(last["Close"], 2)
        )

        c2.metric(
            "RSI",
            round(last["RSI"], 2)
        )

        c3.metric(
            "Score",
            score
        )

        # ==========================================
        # GRAPHIQUE
        # ==========================================

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                name="MASI"
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
                name="BB Haut"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["BB_LOW"],
                name="BB Bas"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

       # ==========================================
        # EXPORT
        # ==========================================

        buffer = BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Analyse",
                index=False
            )

        st.download_button(
            "📥 Télécharger Excel",
            data=buffer.getvalue(),
            file_name="MASI_PRO_V4.xlsx"
        )

    except Exception as e:

        st.error(
            f"Erreur : {str(e)}"
        )

        st.exception(e)
