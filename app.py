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

Exemple :

| Date | Close |
|--------|--------|
| 01/01/2025 | 15000 |
| 02/01/2025 | 15100 |
""")

uploaded_file = st.file_uploader(
    "Importer un fichier Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        # Nettoyage des noms de colonnes
        df.columns = df.columns.str.strip()

        # Vérification des colonnes
        if "Date" not in df.columns:
            st.error("Colonne Date introuvable")
            st.stop()

        if "Close" not in df.columns:
            st.error("Colonne Close introuvable")
            st.write("Colonnes détectées :", df.columns.tolist())
            st.stop()

        # Conversion Date
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        # Conversion robuste de Close
        df["Close"] = (
            df["Close"]
            .astype(str)
            .str.replace("\xa0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )

        df["Close"] = pd.to_numeric(
            df["Close"],
            errors="coerce"
        )

        # Suppression des lignes invalides
        df = df.dropna(
            subset=["Date", "Close"]
        )

        df = df.sort_values(
            "Date"
        ).reset_index(drop=True)

        st.success("Fichier chargé avec succès")

        # ====================
        # Indicateurs techniques
        # ====================

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

        df["RSI"] = ta.momentum.rsi(
            close=df["Close"],
            window=14
        )

        macd = ta.trend.MACD(df["Close"])

        df["MACD"] = macd.macd()
        df["SIGNAL"] = macd.macd_signal()

        # ====================
        # Supports / Résistances
        # ====================

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

        # ====================
        # Graphique principal
        # ====================

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="Cours"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["SMA20"],
                mode="lines",
                name="SMA20"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["SMA50"],
                mode="lines",
                name="SMA50"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["SMA200"],
                mode="lines",
                name="SMA200"
            )
        )

        for s in supports:

            fig.add_hline(
                y=float(s),
                line_color="green",
                line_dash="dot"
            )

        for r in resistances:

            fig.add_hline(
                y=float(r),
                line_color="red",
                line_dash="dash"
            )

        fig.update_layout(
            title="Analyse Chartiste",
            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ====================
        # RSI
        # ====================

        st.subheader("RSI")

        fig_rsi = go.Figure()

        fig_rsi.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["RSI"],
                name="RSI"
            )
        )

        fig_rsi.add_hline(y=70)

        fig_rsi.add_hline(y=30)

        st.plotly_chart(
            fig_rsi,
            use_container_width=True
        )

        # ====================
        # MACD
        # ====================

        st.subheader("MACD")

        fig_macd = go.Figure()

        fig_macd.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MACD"],
                name="MACD"
            )
        )

        fig_macd.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["SIGNAL"],
                name="Signal"
            )
        )

        st.plotly_chart(
            fig_macd,
            use_container_width=True
        )

        # ====================
        # Tableau
        # ====================

        st.subheader("Données")

        st.dataframe(df.tail(50))

    except Exception as e:

        st.error("Erreur détectée")

        st.exception(e)
