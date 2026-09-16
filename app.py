import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from scipy.signal import argrelextrema
from io import BytesIO

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MASI Pro v2",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI Pro v2 - Analyse Technique Avancée")

# --------------------------------------------------
# FONCTIONS
# --------------------------------------------------

def filtrer_niveaux(levels, seuil=0.01):
    niveaux = []

    for lvl in sorted(levels):
        lvl = float(lvl)

        if not niveaux:
            niveaux.append(lvl)

        elif abs(lvl - niveaux[-1]) / niveaux[-1] > seuil:
            niveaux.append(lvl)

    return niveaux


def calculer_score(close,
                    sma20,
                    sma50,
                    sma200,
                    rsi,
                    macd,
                    signal,
                    histo,
                    vol20,
                    position):

    score = 0
    commentaires = []

    # Tendance Long Terme
    if not np.isnan(sma200):

        if close > sma200:
            score += 15
            commentaires.append(
                "✅ Cours supérieur à SMA200 : tendance long terme haussière."
            )
        else:
            commentaires.append(
                "❌ Cours sous SMA200 : tendance long terme fragile."
            )

        if sma50 > sma200:
            score += 15
            commentaires.append(
                "✅ SMA50 au-dessus SMA200 (Golden Zone)."
            )
        else:
            commentaires.append(
                "❌ SMA50 sous SMA200."
            )

    # Momentum

    if sma20 > sma50:
        score += 10
        commentaires.append(
            "✅ SMA20 au-dessus SMA50 : momentum positif."
        )
    else:
        commentaires.append(
            "⚠ SMA20 sous SMA50."
        )

    # MACD

    if macd > signal:
        score += 10
        commentaires.append(
            "✅ MACD supérieur au signal."
        )

    if histo > 0:
        score += 10
        commentaires.append(
            "✅ Histogramme MACD positif."
        )

    # RSI

    if 45 <= rsi <= 65:
        score += 15
        commentaires.append(
            f"✅ RSI équilibré ({rsi:.1f})."
        )

    elif 35 <= rsi < 45 or 65 < rsi <= 75:
        score += 10
        commentaires.append(
            f"⚠ RSI intermédiaire ({rsi:.1f})."
        )

    elif rsi < 35:
        score += 5
        commentaires.append(
            f"⚠ RSI survendu ({rsi:.1f})."
        )

    # Position Range

    if not np.isnan(position):

        if position > 70:
            score += 15
            commentaires.append(
                "✅ Position forte dans le range 20 jours."
            )

        elif position > 50:
            score += 10
            commentaires.append(
                "✅ Position favorable dans le range."
            )

        elif position > 30:
            score += 5

    # Volatilité

    if vol20 < 0.15:
        score += 10
        commentaires.append(
            "✅ Faible volatilité."
        )

    elif vol20 < 0.25:
        score += 5
        commentaires.append(
            "⚠ Volatilité modérée."
        )

    return score, commentaires


def opinion(score):

    if score >= 80:
        return "🟢 ACHAT FORT"

    if score >= 65:
        return "✅ ACHAT"

    if score >= 50:
        return "🔵 CONSERVATION"

    if score >= 35:
        return "🟠 VIGILANCE"

    return "🔴 VENTE"


# --------------------------------------------------
# CHARGEMENT FICHIER
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Importer le fichier Excel",
    type=["xlsx"]
)

if uploaded_file:

    try:

        excel = pd.ExcelFile(uploaded_file)

        feuilles = excel.sheet_names

        st.success(
            f"Feuilles détectées : {', '.join(feuilles)}"
        )

        if "Data_masi" not in feuilles:

            st.error(
                "Feuille 'Data_masi' introuvable."
            )

            st.stop()

        # Lecture forcée

        df = pd.read_excel(
            uploaded_file,
            sheet_name="Data_masi"
        )

        # --------------------------------------
        # Nettoyage
        # --------------------------------------

        df.columns = df.columns.str.strip()

        if "Date" not in df.columns:
            st.error("Colonne Date manquante")
            st.stop()

        if "Close" not in df.columns:
            st.error("Colonne Close manquante")
            st.stop()

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

        df.dropna(
            subset=["Date", "Close"],
            inplace=True
        )

        df.sort_values(
            "Date",
            inplace=True
        )

        df.reset_index(
            drop=True,
            inplace=True
        )

        # --------------------------------------
        # INDICATEURS
        # --------------------------------------

        df["SMA20"] = ta.trend.sma_indicator(
            df["Close"],
            window=20
        )

        df["SMA50"] = ta.trend.sma_indicator(
            df["Close"],
            window=50
        )

        if len(df) >= 200:
            df["SMA200"] = ta.trend.sma_indicator(
                df["Close"],
                window=200
            )
        else:
            df["SMA200"] = np.nan

        df["RSI"] = ta.momentum.rsi(
            df["Close"],
            window=14
        )

        macd_obj = ta.trend.MACD(df["Close"])

        df["MACD"] = macd_obj.macd()
        df["SIGNAL"] = macd_obj.macd_signal()

        df["HISTO"] = (
            df["MACD"] - df["SIGNAL"]
        )

        bb = ta.volatility.BollingerBands(
            df["Close"],
            window=20,
            window_dev=2
        )

        df["BB_HAUT"] = bb.bollinger_hband()
        df["BB_BAS"] = bb.bollinger_lband()
        df["BB_MILIEU"] = bb.bollinger_mavg()

        # Volatilité

        df["Rendement"] = np.log(
            df["Close"] / df["Close"].shift(1)
        )

        df["Vol20"] = (
            df["Rendement"]
            .rolling(20)
            .std()
            * np.sqrt(252)
        )

        df["PlusHaut20"] = (
            df["Close"]
            .rolling(20)
            .max()
        )

        df["PlusBas20"] = (
            df["Close"]
            .rolling(20)
            .min()
        )

        # --------------------------------------
        # SUPPORTS / RESISTANCES
        # --------------------------------------

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

        supports = filtrer_niveaux(
            prices[minima]
        )

        resistances = filtrer_niveaux(
            prices[maxima]
        )

        # --------------------------------------
        # DERNIERS INDICATEURS
        # --------------------------------------

        close = df["Close"].iloc[-1]
        sma20 = df["SMA20"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1]
        sma200 = df["SMA200"].iloc[-1]
        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]
        signal = df["SIGNAL"].iloc[-1]
        histo = df["HISTO"].iloc[-1]
        vol20 = df["Vol20"].iloc[-1]

        ph20 = df["PlusHaut20"].iloc[-1]
        pb20 = df["PlusBas20"].iloc[-1]

        position = np.nan

        if ph20 != pb20:
            position = (
                (close - pb20)
                / (ph20 - pb20)
            ) * 100

        score, commentaires = calculer_score(
            close,
            sma20,
            sma50,
            sma200,
            rsi,
            macd,
            signal,
            histo,
            vol20,
            position
        )

        avis = opinion(score)

        # --------------------------------------
        # SCORE
        # --------------------------------------

        st.header("🎯 Score Technique")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Score",
            f"{score}/100"
        )

        c2.metric(
            "RSI",
            f"{rsi:.1f}"
        )

        c3.metric(
            "Position Range",
            f"{position:.0f}%"
        )

        st.subheader("Opinion")

        st.markdown(
            f"## {avis}"
        )

        # --------------------------------------
        # COMMENTAIRES
        # --------------------------------------

        st.subheader(
            "🧠 Commentaires Automatiques"
        )

        for c in commentaires:
            st.write(c)

        # --------------------------------------
        # GRAPHIQUE PRINCIPAL
        # --------------------------------------

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

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["BB_HAUT"],
                name="BB Haut"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["BB_BAS"],
                name="BB Bas"
            )
        )

        for s in supports[-5:]:
            fig.add_hline(
                y=s,
                line_color="green",
                line_dash="dot"
            )

        for r in resistances[-5:]:
            fig.add_hline(
                y=r,
                line_color="red",
                line_dash="dash"
            )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------
        # RSI
        # --------------------------------------

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

        # --------------------------------------
        # MACD
        # --------------------------------------

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

        fig_macd.add_bar(
            x=df["Date"],
            y=df["HISTO"],
            name="Histogramme"
        )

        st.plotly_chart(
            fig_macd,
            use_container_width=True
        )

        # --------------------------------------
        # SUPPORTS / RESISTANCES
        # --------------------------------------

        st.subheader(
            "📍 Supports / Résistances"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write("Supports")
            st.write(
                supports[-10:]
            )

        with col2:
            st.write("Résistances")
            st.write(
                resistances[-10:]
            )

        # --------------------------------------
        # TABLEAU
        # --------------------------------------

        st.subheader(
            "📋 Données calculées"
        )

        st.dataframe(
            df.tail(100),
            use_container_width=True
        )

        # --------------------------------------
        # EXPORT EXCEL
        # --------------------------------------

        buffer = BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Analyse_MASI",
                index=False
            )

        st.download_button(
            label="📥 Télécharger Analyse Excel",
            data=buffer.getvalue(),
            file_name="Analyse_MASI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Erreur : {str(e)}"
        )

        st.exception(e)
