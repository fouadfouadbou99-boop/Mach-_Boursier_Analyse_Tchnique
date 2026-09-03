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

st.markdown("""
Chargez un fichier Excel contenant :

- Date
- Close

L'application calcule automatiquement :

✅ SMA20

✅ SMA50

✅ SMA200

✅ RSI

✅ MACD

✅ Supports

✅ Résistances

✅ Analyse commentée
""")

# =====================================================
# IMPORT FICHIER
# =====================================================

uploaded_file = st.file_uploader(
    "Importer le fichier Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        df.columns = df.columns.str.strip()

        if "Date" not in df.columns:
            st.error("Colonne Date introuvable.")
            st.stop()

        if "Close" not in df.columns:
            st.error("Colonne Close introuvable.")
            st.write(df.columns.tolist())
            st.stop()

        # =====================================================
        # PREPARATION DONNEES
        # =====================================================

        df["Date"] = pd.to_datetime(
            df["Date"],
            dayfirst=True,
            errors="coerce"
        )

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

        df = df.dropna(
            subset=["Date", "Close"]
        )

        df = (
            df.sort_values("Date")
            .reset_index(drop=True)
        )

        st.success("Fichier chargé avec succès")

        # =====================================================
        # CONTROLE DES DATES
        # =====================================================

        st.info(
            f"Dernière date disponible : {df['Date'].max().strftime('%d/%m/%Y')}"
        )

        # =====================================================
        # INDICATEURS TECHNIQUES
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

        df["RSI"] = ta.momentum.rsi(
            close=df["Close"],
            window=14
        )

        macd_obj = ta.trend.MACD(df["Close"])

        df["MACD"] = macd_obj.macd()

        df["SIGNAL"] = macd_obj.macd_signal()

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
        # GRAPHIQUE PRINCIPAL
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
            title="Analyse Chartiste",
            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =====================================================
        # RSI
        # =====================================================

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

        # =====================================================
        # MACD
        # =====================================================

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
                name="SIGNAL"
            )
        )

        st.plotly_chart(
            fig_macd,
            use_container_width=True
        )

        # =====================================================
        # ANALYSE COMMENTEE
        # =====================================================

        dernier_cours = df["Close"].iloc[-1]

        sma20 = df["SMA20"].iloc[-1]

        sma50 = df["SMA50"].iloc[-1]

        rsi = df["RSI"].iloc[-1]

        macd = df["MACD"].iloc[-1]

        signal = df["SIGNAL"].iloc[-1]

        st.header("🧠 Analyse Technique")

        commentaire = f"""
Le MASI clôture à **{dernier_cours:,.2f}** points.

La SMA20 est de **{sma20:,.2f}**.

La SMA50 est de **{sma50:,.2f}**.

Le RSI est de **{rsi:.2f}**.

Le MACD est de **{macd:.2f}**.
"""

        if sma20 > sma50:

            commentaire += """

✅ La dynamique de court terme reste haussière.
"""

        else:

            commentaire += """

⚠️ La dynamique de court terme reste baissière.
"""

        if rsi > 70:

            commentaire += """

Le marché est actuellement en situation de surachat.
"""

        elif rsi < 30:

            commentaire += """

Le marché est actuellement en situation de survente.
"""

        else:

            commentaire += """

Le RSI évolue dans une zone neutre.
"""

        if macd > signal:

            commentaire += """

Le momentum reste positif.
"""

        else:

            commentaire += """

Le momentum montre un ralentissement.
"""

        st.info(commentaire)

        # =====================================================
        # OPINION
        # =====================================================

        st.header("🎯 Opinion Technique")

        if sma20 > sma50 and macd > signal and rsi < 70:

            st.success(
                "ACHAT / CONSERVATION"
            )

      
