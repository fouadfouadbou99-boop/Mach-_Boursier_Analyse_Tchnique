import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from scipy.signal import argrelextrema

st.set_page_config(
    page_title="Analyse Chartiste",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Analyse Chartiste Automatique")

st.markdown("""
Chargez un fichier Excel contenant au minimum :

- Date
- Close

L'application calcule :
- SMA 20
- SMA 50
- SMA 200
- RSI
- MACD
- Supports
- Résistances
""")

uploaded_file = st.file_uploader(
    "Importer un fichier Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        st.success("Fichier chargé avec succès")

        if "Date" not in df.columns:
            st.error("Colonne 'Date' absente")
            st.stop()

        if "Close" not in df.columns:
            st.error("Colonne 'Close' absente")
            st.stop()

        df["Date"] = pd.to_datetime(df["Date"])

        if df["Close"].dtype == object:

            df["Close"] = (
                df["Close"]
                .astype(str)
                .str.replace(" ", "")
                .str.replace(",", ".")
            )

            df["Close"] = pd.to_numeric(df["Close"])

        df = df.sort_values("Date").reset_index(drop=True)

        # =====================
        # MOYENNES MOBILES
        # =====================

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

        # =====================
        # RSI
        # =====================

        df["RSI"] = ta.momentum.rsi(
            df["Close"],
            window=14
        )

        # =====================
        # MACD
        # =====================

        macd = ta.trend.MACD(df["Close"])

        df["MACD"] = macd.macd()

        df["Signal"] = macd.macd_signal()

        # =====================
        # SUPPORTS / RESISTANCES
        # =====================

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

        # =====================
        # GRAPHIQUE PRINCIPAL
        # =====================

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                name="Cours",
                line=dict(color="blue")
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

        for support in supports:

            fig.add_hline(
                y=support,
                line_dash="dot",
                line_color="green"
            )

        for resistance in resistances:

            fig.add_hline(
                y=resistance,
                line_dash="dash",
                line_color="red"
            )

        fig.update_layout(
            title="Analyse Chartiste",
            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =====================
        # RSI
        # =====================

        st.subheader("RSI")

        rsi_fig = go.Figure()

        rsi_fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["RSI"],
                name="RSI"
            )
        )

        rsi_fig.add_hline(y=70)

        rsi_fig.add_hline(y=30)

        st.plotly_chart(
            rsi_fig,
            use_container_width=True
        )

        # =====================
        # MACD
        # =====================

        st.subheader("MACD")

        macd_fig = go.Figure()

        macd_fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MACD"],
                name="MACD"
            )
        )

        macd_fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Signal"],
                name="Signal"
            )
        )

        st.plotly_chart(
            macd_fig,
            use_container_width=True
        )

        st.subheader("Données")

        st.dataframe(df)

    except Exception as e:

        st.exception(e)
