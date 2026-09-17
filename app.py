# MASI PRO V8
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import ta

st.set_page_config(page_title="MASI PRO V8", page_icon="📈", layout="wide")
st.title("📈 MASI PRO V8")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name="Data_masi", engine="openpyxl")
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Close"] = pd.to_numeric(df["Close"])
    return df.sort_values("Date").reset_index(drop=True)


def calculate_excel_rsi(close, period=14):
    variation = close.pct_change()
    gain = variation.clip(lower=0)
    loss = (-variation.clip(upper=0))
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


@st.cache_data
def prepare(df):
    d = df.copy()
    d["SMA20"] = ta.trend.sma_indicator(d["Close"], 20)
    d["SMA50"] = ta.trend.sma_indicator(d["Close"], 50)
    d["SMA200"] = ta.trend.sma_indicator(d["Close"], 200)
    d["RSI"] = calculate_excel_rsi(d["Close"], 14)
    macd = ta.trend.MACD(d["Close"])
    d["MACD"] = macd.macd()
    d["SIGNAL"] = macd.macd_signal()
    d["HISTO"] = d["MACD"] - d["SIGNAL"]
    bb = ta.volatility.BollingerBands(d["Close"], window=20, window_dev=2)
    d["BB_UP"] = bb.bollinger_hband()
    d["BB_LOW"] = bb.bollinger_lband()
    return d

uploaded = st.file_uploader("Importer Data_masi.xlsx", type=["xlsx"])

if uploaded:
    raw = load_data(uploaded)
    df = prepare(raw).dropna().reset_index(drop=True)

    if df.empty:
        st.error("Pas assez de données pour calculer les indicateurs.")
        st.stop()

    last = df.iloc[-1]
    ref = raw[raw["Date"] <= pd.Timestamp(year=last["Date"].year-1, month=12, day=31)].iloc[-1]
    ytd = ((last["Close"] / ref["Close"]) - 1) * 100

    score = 0
    score += 25 if last["Close"] > last["SMA200"] else 0
    score += 25 if last["SMA50"] > last["SMA200"] else 0
    score += 20 if last["SMA20"] > last["SMA50"] else 0
    score += 15 if last["MACD"] > last["SIGNAL"] else 0
    score += 15 if last["RSI"] > 60 else (10 if last["RSI"] > 40 else 5)

    support_20 = float(raw["Close"].tail(20).min())
    resistance_20 = float(raw["Close"].tail(20).max())
    support_60 = float(raw["Close"].tail(60).min())
    resistance_60 = float(raw["Close"].tail(60).max())
    support_200 = float(raw["Close"].tail(200).min())
    resistance_200 = float(raw["Close"].tail(200).max())

    st.subheader("Supports / Résistances")
    st.dataframe(pd.DataFrame({
        "20 Jours":[support_20,resistance_20],
        "60 Jours":[support_60,resistance_60],
        "200 Jours":[support_200,resistance_200]
    }, index=["Support","Résistance"]))
