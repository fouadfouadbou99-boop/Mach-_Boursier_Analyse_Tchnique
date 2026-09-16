import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta

from io import BytesIO
from scipy.signal import argrelextrema

# ====================================================
# CONFIGURATION
# ====================================================

st.set_page_config(
    page_title="MASI Pro V3",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI Pro V3")
st.markdown("Analyse Technique Automatique du MASI")

# ====================================================
# FONCTIONS
# ====================================================

def filtrer_niveaux(levels, seuil=0.01):

    niveaux = []

    for lvl in sorted(levels):

        lvl = float(lvl)

        if not niveaux:
            niveaux.append(lvl)

        elif abs(lvl - niveaux[-1]) / niveaux[-1] > seuil:
            niveaux.append(lvl)

    return niveaux


def calculer_score(
        close,
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

    # Long terme

    if not np.isnan(sma200):

        if close > sma200:
            score += 20
            commentaires.append(
                "✅ Cours supérieur à SMA200."
            )

        else:
            commentaires.append(
                "❌ Cours sous SMA200."
            )

        if sma50 > sma200:
            score += 15
            commentaires.append(
                "✅ SMA50 > SMA200."
            )

        else:
            commentaires.append(
                "❌ SMA50 < SMA200."
            )

    # Court terme

    if sma20 > sma50:
        score += 10
        commentaires.append(
            "✅ SMA20 > SMA50."
        )

    # MACD

    if macd > signal:
        score += 15
        commentaires.append(
            "✅ MACD haussier."
        )

    if histo > 0:
        score += 5

    # RSI

    if 45 <= rsi <= 65:
        score += 15
        commentaires.append(
            f"✅ RSI équilibré ({rsi:.1f})."
        )

    elif 35 <= rsi < 45:
        score += 10

    elif rsi < 35:
        score += 5

    # Range

    if position > 70:
        score += 15

    elif position > 50:
        score += 10

    elif position > 30:
        score += 5

    # Volatilité

    if vol20 < 0.15:
        score += 10

    elif vol20 < 0.25:
        score += 5

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


def rapport_technique(
        close,
        score,
        avis,
        rsi,
        macd,
        signal,
        sma20,
        sma50,
        sma200,
        support,
        resistance):

    texte = f"""
RAPPORT TECHNIQUE MASI

Date : {pd.Timestamp.now():%d/%m/%Y}

------------------------------------

Cours actuel : {close:,.2f}

Score technique : {score}/100

Opinion : {avis}

------------------------------------

TENDANCE

Court terme :
{'Haussière' if sma20 > sma50 else 'Baissière'}

Moyen terme :
{'Haussière' if sma50 > sma200 else 'Baissière'}

Long terme :
{'Haussière' if close > sma200 else 'Baissière'}

------------------------------------

MOMENTUM

RSI : {rsi:.2f}

MACD : {macd:.2f}

Signal : {signal:.2f}

------------------------------------

SUPPORT PROCHE

{support}

RESISTANCE PROCHE

{resistance}

------------------------------------

CONCLUSION

{avis}
"""

    return texte


# ====================================================
# CHARGEMENT
# ====================================================

uploaded_file = st.file_uploader(
    "Importer Excel",
    type=["xlsx"]
)

if uploaded_file:

    try:

        excel = pd.ExcelFile(uploaded_file)

        st.success(
            f"Feuilles : {', '.join(excel.sheet_names)}"
        )

        if "Data_masi" not in excel.sheet_names:

            st.error(
                "Feuille Data_masi introuvable"
            )

            st.stop()

        df = pd.read_excel(
            uploaded_file,
            sheet_name="Data_masi"
        )

        df.columns = df.columns.str.strip()

        required_cols = [
            "Date",
            "Close"
        ]

        for col in required_cols:

            if col not in df.columns:
                st.error(
                    f"Colonne manquante : {col}"
                )
                st.stop()

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        df["Close"] = (
            df["Close"]
            .astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
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

        # ====================================================
        # INDICATEURS
        # ====================================================

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

        macd_obj = ta.trend.MACD(df["Close"])

        df["MACD"] = macd_obj.macd()

        df["SIGNAL"] = (
            macd_obj.macd_signal()
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

        df["BB_HAUT"] = \
            bb.bollinger_hband()

        df["BB_BAS"] = \
            bb.bollinger_lband()

        df["BB_MID"] = \
            bb.bollinger_mavg()

        # ====================================================
        # VOLATILITE
        # ====================================================

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

        df["PLUS_HAUT20"] = (
            df["Close"]
            .rolling(20)
            .max()
        )

        df["PLUS_BAS20"] = (
            df["Close"]
            .rolling(20)
            .min()
        )

        # ====================================================
        # SUPPORTS RESISTANCES
        # ====================================================

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

        close = df["Close"].iloc[-1]

        supports_valides = [
            s for s in supports
            if s < close
        ]

        resistances_valides = [
            r for r in resistances
            if r > close
        ]

        support_proche = (
            max(supports_valides)
            if supports_valides
            else None
        )

        resistance_proche = (
            min(resistances_valides)
            if resistances_valides
            else None
        )

        # ====================================================
        # DERNIERS INDICATEURS
        # ====================================================

        sma20 = df["SMA20"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1]
        sma200 = df["SMA200"].iloc[-1]

        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]
        signal = df["SIGNAL"].iloc[-1]
        histo = df["HISTO"].iloc[-1]

        vol20 = df["VOL20"].iloc[-1]

        ph20 = df["PLUS_HAUT20"].iloc[-1]
        pb20 = df["PLUS_BAS20"].iloc[-1]

        position = 50

        if (
                pd.notna(ph20)
                and pd.notna(pb20)
                and ph20 > pb20
        ):

            position = (
                (close - pb20)
                / (ph20 - pb20)
            ) * 100

            position = max(
                0,
                min(100, position)
            )

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

        # ====================================================
        # GOLDEN CROSS
        # ====================================================

        if len(df) > 220:

            prev50 = df["SMA50"].iloc[-2]
            prev200 = df["SMA200"].iloc[-2]

            if (
                    prev50 < prev200
                    and sma50 > sma200
            ):
                commentaires.append(
                    "🚀 Golden Cross détecté"
                )

            if (
                    prev50 > prev200
                    and sma50 < sma200
            ):
                commentaires.append(
                    "⚠ Death Cross détecté"
                )

        # ====================================================
        # RAPPORT
        # ====================================================

        rapport = rapport_technique(
            close,
            score,
            avis,
            rsi,
            macd,
            signal,
            sma20,
            sma50,
            sma200,
            support_proche,
            resistance_proche
        )

        # ====================================================
        # SCORE
        # ====================================================

        st.header("🎯 Score Technique")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Score",
            f"{score}/100"
        )

        col2.metric(
            "RSI",
            f"{rsi:.1f}"
        )

        col3.metric(
            "Position",
            f"{position:.1f}%"
        )

        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={
                    "text":
                    "Score Technique"
                },
                gauge={
                    "axis":
                        {"range": [0, 100]}
                }
            )
        )

        st.plotly_chart(
            gauge,
            use_container_width=True
        )

        st.markdown(
            f"## {avis}"
        )

        st.subheader(
            "📝 Commentaires"
        )

        for c in commentaires:
            st.write(c)

        st.subheader(
            "📑 Rapport Technique"
        )

        st.text(rapport)

        # ====================================================
        # GRAPHIQUE PRINCIPAL
        # ====================================================

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

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ====================================================
        # RSI
        # ====================================================

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

        # ====================================================
        # MACD
        # ====================================================

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

        # ====================================================
        # EXPORTS
        # ====================================================

        buffer = BytesIO()

        with pd.ExcelWriter(
                buffer,
                engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Indicateurs",
                index=False
            )

            pd.DataFrame(
                {"Supports": supports}
            ).to_excel(
                writer,
                sheet_name="Supports",
                index=False
            )

            pd.DataFrame(
                {"Resistances": resistances}
            ).to_excel(
                writer,
                sheet_name="Resistances",
                index=False
            )

            pd.DataFrame(
                {"Rapport": [rapport]}
            ).to_excel(
                writer,
                sheet_name="Rapport",
                index=False
            )

        st.download_button(
            "📥 Télécharger Excel",
            data=buffer.getvalue(),
            file_name="MASI_PRO_V3.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            "📄 Télécharger Rapport TXT",
            rapport,
            file_name="Rapport_MASI.txt",
            mime="text/plain"
        )

    except Exception as e:

        st.error(
            f"Erreur : {str(e)}"
        )

        st.exception(e)
