# ==========================================================
# MASI PRO V8
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from io import BytesIO

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="MASI PRO V8",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI PRO V8")

# ==========================================================
# CHARGEMENT
# ==========================================================

@st.cache_data
def load_data(file):

    df = pd.read_excel(
        file,
        sheet_name="Data_masi",
        engine="openpyxl"
    )

    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Close"] = pd.to_numeric(df["Close"])

    df = df.sort_values("Date")

    return df.reset_index(drop=True)

# ==========================================================
# RSI
# ==========================================================

def calculate_excel_rsi(close, period=14):

    variation = close.pct_change()

    gain = variation.clip(lower=0)
    loss = (-variation.clip(upper=0))

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ==========================================================
# INDICATEURS
# ==========================================================

@st.cache_data
def prepare(df):

    d = df.copy()

    d["SMA20"] = ta.trend.sma_indicator(
        d["Close"],
        window=20
    )

    d["SMA50"] = ta.trend.sma_indicator(
        d["Close"],
        window=50
    )

    d["SMA200"] = ta.trend.sma_indicator(
        d["Close"],
        window=200
    )

    d["RSI"] = calculate_excel_rsi(
        d["Close"],
        14
    )

    macd = ta.trend.MACD(
        d["Close"]
    )

    d["MACD"] = macd.macd()

    d["SIGNAL"] = macd.macd_signal()

    d["HISTO"] = (
        d["MACD"]
        - d["SIGNAL"]
    )

    bb = ta.volatility.BollingerBands(
        d["Close"],
        window=20,
        window_dev=2
    )

    d["BB_UP"] = bb.bollinger_hband()
    d["BB_LOW"] = bb.bollinger_lband()

    return d

# ==========================================================
# SUPPORTS / RESISTANCES
# ==========================================================

def support_resistance(df, horizon):

    subset = df.tail(
        min(horizon, len(df))
    )

    support = float(
        subset["Close"].min()
    )

    resistance = float(
        subset["Close"].max()
    )

    return support, resistance

# ==========================================================
# PERFORMANCE
# ==========================================================

def performance(df, days):

    if len(df) <= days:
        return np.nan

    current = df.iloc[-1]["Close"]

    old = df.iloc[-days]["Close"]

    return ((current / old) - 1) * 100

# ==========================================================
# UPLOAD
# ==========================================================

uploaded = st.file_uploader(
    "Importer Data_masi.xlsx",
    type=["xlsx"]
)

if uploaded:

    raw = load_data(uploaded)

    df = prepare(raw)

    df = df.dropna().reset_index(drop=True)

    last = df.iloc[-1]

    # ======================================================
    # YTD
    # ======================================================

    previous_year = raw[
        raw["Date"] <= pd.Timestamp(
            year=last["Date"].year - 1,
            month=12,
            day=31
        )
    ]

    if len(previous_year):

        ref = previous_year.iloc[-1]

        ytd = (
            (
                last["Close"]
                /
                ref["Close"]
            ) - 1
        ) * 100

    else:

        ref = raw.iloc[0]

        ytd = np.nan

    # ======================================================
    # PERFORMANCE
    # ======================================================

    r1 = performance(df, 21)
    r3 = performance(df, 63)
    r6 = performance(df, 126)
    r12 = performance(df, 252)

    # ======================================================
    # SCORE
    # ======================================================

    score = 0

    score += 25 if last["Close"] > last["SMA200"] else 0

    score += 25 if last["SMA50"] > last["SMA200"] else 0

    score += 20 if last["SMA20"] > last["SMA50"] else 0

    score += 15 if last["MACD"] > last["SIGNAL"] else 0

    score += (
        15
        if last["RSI"] > 60
        else (10 if last["RSI"] > 40 else 5)
    )

    if score >= 75:
        reco = "✅ ACHAT"
    elif score >= 45:
        reco = "⚠️ SURVEILLER"
    else:
        reco = "❌ ATTENDRE"

    # ======================================================
    # S/R
    # ======================================================

    support_20, resistance_20 = support_resistance(df, 20)

    support_60, resistance_60 = support_resistance(df, 60)

    support_200, resistance_200 = support_resistance(df, 200)

    # ======================================================
    # TABS
    # ======================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "Dashboard",
        "Analyse",
        "Export",
        "Comité"
    ])

    # ======================================================
    # DASHBOARD
    # ======================================================

   with tab1:

        c1, c2, c3, c4, c5 = st.columns(5)
    
        c1.metric("Cours", f"{last.Close:.2f}")
        c2.metric("RSI", f"{last.RSI:.2f}")
        c3.metric("Score", f"{score}/100")
        c4.metric("YTD", f"{ytd:.2f}%")
        c5.metric("Signal", reco)
    
        p1, p2, p3, p4 = st.columns(4)
    
        p1.metric("1M", f"{r1:.2f}%")
        p2.metric("3M", f"{r3:.2f}%")
        p3.metric("6M", f"{r6:.2f}%")
        p4.metric("1Y", f"{r12:.2f}%")
    
        st.subheader("Supports / Résistances")
    
        s1, s2, s3 = st.columns(3)

        with s1:
            st.metric("Support 20j", f"{support_20:.2f}")
            st.metric("Résistance 20j", f"{resistance_20:.2f}")

        with s2:
            st.metric("Support 60j", f"{support_60:.2f}")
            st.metric("Résistance 60j", f"{resistance_60:.2f}")

        with s3:
            st.metric("Support 200j", f"{support_200:.2f}")
            st.metric("Résistance 200j", f"{resistance_200:.2f}")

    # ======================================================
    # ANALYSE
    # ======================================================

    with tab2:

        fig = go.Figure()

        for col in [
            "Close",
            "SMA20",
            "SMA50",
            "SMA200",
            "BB_UP",
            "BB_LOW"
        \]:

            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df[col],
                    name=col
                )
            )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        rsi_fig = go.Figure()

        rsi_fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["RSI"],
                name="RSI"
            )
        )

        st.plotly_chart(
            rsi_fig,
            use_container_width=True
        )

    # ======================================================
    # EXPORT
    # ======================================================

    with tab3:

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

            pd.DataFrame({
                "Score": [score],
                "YTD": [ytd],
                "Support20": [support_20],
                "Resistance20": [resistance_20],
                "Support60": [support_60],
                "Resistance60": [resistance_60],
                "Support200": [support_200],
                "Resistance200": [resistance_200]
            }).to_excel(
                writer,
                sheet_name="Dashboard",
                index=False
            )

        st.download_button(
            "Télécharger le rapport",
            data=buffer.getvalue(),
            file_name="MASI_PRO_V8.xlsx"
        )

    # ======================================================
    # COMITE
    # ======================================================

    with tab4:

        commentaire = f"""
### Synthèse Comité

Date : {last['Date'].strftime('%d/%m/%Y')}

Cours : {last['Close'\]:.2f}

Performance YTD : {ytd:.2f} %

Score Technique : {score}/100

Recommandation :
{reco}

Supports / Résistances :

20 jours :
- Support : {support_20:.2f}
- Résistance : {resistance_20:.2f}

60 jours :
- Support : {support_60:.2f}
- Résistance : {resistance_60:.2f}

200 jours :
- Support : {support_200:.2f}
- Résistance : {resistance_200:.2f}
"""

        st.markdown(commentaire)
