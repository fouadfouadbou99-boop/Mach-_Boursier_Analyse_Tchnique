import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from scipy.signal import argrelextrema

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Analyse Chartiste Automatique",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Analyse Chartiste Automatique")

# =====================================================
# IMPORT
# =====================================================

uploaded_file = st.file_uploader(
    "Importer un fichier Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        df.columns = df.columns.str.strip()

        if "Date" not in df.columns:
            st.error("Colonne Date introuvable")
            st.stop()

        if "Close" not in df.columns:
            st.error("Colonne Close introuvable")
            st.write(df.columns.tolist())
            st.stop()

        # =====================================================
        # NETTOYAGE
        # =====================================================

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        df["Close"] = (
            df["Close"]
            .astype(str)
            .str.replace("\xa0", "", regex=False)
            .str.replace(" ", "", regex=False)
        )

        df["Close"] = pd.to_numeric(
            df["Close"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["Date", "Close"]
        )

        df = df.sort_values(
            "Date"
        ).reset_index(drop=True)

        st.success("Fichier chargé avec succès")

        # =====================================================
        # INDICATEURS
        # =====================================================

        df["SMA20"] = ta.trend.sma_indicator(
            close=df["Close"],
            window=20
        )

        df["SMA50"] = ta.trend.sma_indicator(
            close=df["Close"],
            window=50
        )

        df["SMA200"] = ta.trend.sma_indicator(
            close=df["Close"],
            window=200
        )

        rsi_indicator = ta.momentum.RSIIndicator(
            close=df["Close"],
            window=14
        )

        df["RSI"] = rsi_indicator.rsi()

        macd = ta.trend.MACD(
            close=df["Close"],
            window_slow=26,
            window_fast=12,
            window_sign=9
        )

        df["MACD"] = macd.macd()
        df["SIGNAL"] = macd.macd_signal()

        # =====================================================
        # CONTROLE DES INDICATEURS
        # =====================================================

        st.subheader("🔍 Contrôle indicateurs")

        controle = pd.DataFrame({
            "Indicateur": [
                "Cours",
                "SMA20",
                "SMA50",
                "SMA200",
                "RSI",
                "MACD",
                "Signal"
            ],
            "Valeur": [
                round(df["Close"].iloc[-1], 2),
                round(df["SMA20"].iloc[-1], 2),
                round(df["SMA50"].iloc[-1], 2),
                round(df["SMA200"].iloc[-1], 2),
                round(df["RSI"].iloc[-1], 2),
                round(df["MACD"].iloc[-1], 2),
                round(df["SIGNAL"].iloc[-1], 2)
            ]
        })

        st.dataframe(
            controle,
            use_container_width=True,
            hide_index=True
        )

        # =====================================================
        # SUPPORTS / RESISTANCES
        # =====================================================

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

        # =====================================================
        # GRAPHIQUE
        # =====================================================

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                name="Cours"
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

        fig.update_layout(
            height=700,
            title="Analyse Chartiste"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =====================================================
        # ANALYSE AUTOMATIQUE
        # =====================================================

        dernier_cours = float(df["Close"].iloc[-1])
        sma20 = float(df["SMA20"].iloc[-1])
        sma50 = float(df["SMA50"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])
        macd_value = float(df["MACD"].iloc[-1])
        signal = float(df["SIGNAL"].iloc[-1])

        support_proche = max(
            [s for s in supports if s < dernier_cours],
            default=np.nan
        )

        resistance_proche = min(
            [r for r in resistances if r > dernier_cours],
            default=np.nan
        )

        commentaire = f"""
### Synthèse

Le dernier cours observé est de **{dernier_cours:,.2f}** points.

"""

        if sma20 > sma50:
            commentaire += """
✅ La moyenne mobile 20 jours est supérieure à la moyenne mobile 50 jours.

La tendance de court terme demeure haussière.

"""
        else:
            commentaire += """
⚠️ La moyenne mobile 20 jours est inférieure à la moyenne mobile 50 jours.

La tendance de court terme demeure baissière.

"""

        if rsi > 70:
            commentaire += f"""
Le RSI est de **{rsi:.1f}**.

Le marché se situe en zone de surachat.

"""
        elif rsi < 30:
            commentaire
