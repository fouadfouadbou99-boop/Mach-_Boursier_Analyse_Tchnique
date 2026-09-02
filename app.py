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
Chargez un fichier Excel contenant au minimum :

- Date
- Close

L'application génère :

✅ Graphique interactif

✅ Supports & Résistances

✅ RSI

✅ MACD

✅ Analyse automatique commentée
""")

# =====================================================
# IMPORT FICHIER
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

        df = df.sort_values(
            "Date"
        ).reset_index(drop=True)

        st.success("Fichier chargé avec succès")

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
                name="Signal"
            )
        )

        st.plotly_chart(
            fig_macd,
            use_container_width=True
        )

        # =====================================================
        # ANALYSE COMMENTEE
        # =====================================================

        st.header("🧠 Analyse Automatique")

        dernier_cours = df["Close"].iloc[-1]
        sma20 = df["SMA20"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1]
        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]
        signal = df["SIGNAL"].iloc[-1]

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

            commentaire += f"""
Le RSI est de **{rsi:.1f}**.

Le marché se situe en zone de survente.
"""

        else:

            commentaire += f"""
Le RSI est de **{rsi:.1f}**.

Le marché se situe dans une zone neutre.
"""

        if macd > signal:

            commentaire += """

Le MACD évolue au-dessus de sa ligne de signal.

Le momentum reste positif.
"""

        else:

            commentaire += """

Le MACD évolue sous sa ligne de signal.

Le momentum reste négatif.
"""

        if not np.isnan(support_proche):

            commentaire += f"""

**Support principal : {support_proche:,.0f} points**
"""

        if not np.isnan(resistance_proche):

            commentaire += f"""

**Résistance principale : {resistance_proche:,.0f} points**
"""

        st.info(commentaire)

        # =====================================================
        # RECOMMANDATION
        # =====================================================

        st.header("🎯 Opinion Technique")

        if sma20 > sma50 and macd > signal and rsi < 70:

            st.success(
                "ACHAT / CONSERVATION : les indicateurs restent globalement favorables."
            )

        elif sma20 < sma50 and macd < signal:

            st.error(
                "VIGILANCE : les indicateurs affichent un biais baissier."
            )

        else:

            st.warning(
                "NEUTRE : marché en phase d'hésitation ou de consolidation."
            )

        # =====================================================
        # DONNEES
        # =====================================================

        st.subheader("Données")

        st.dataframe(
            df.tail(50),
            use_container_width=True
        )

    except Exception as e:

        st.error("Erreur détectée")

        st.exception(e)
