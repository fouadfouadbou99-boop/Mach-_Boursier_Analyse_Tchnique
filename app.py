# MASI PRO V7

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from scipy.signal import argrelextrema
import ta

st.set_page_config(
    page_title="MASI PRO V7",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MASI PRO V7")

# ==========================================================
# Chargement des données
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

    return df.sort_values("Date").reset_index(drop=True)

# ==========================================================
# Calcul des indicateurs
# ==========================================================

@st.cache_data
def prepare(df):

    d = df.copy()

    d["SMA20"] = ta.trend.sma_indicator(d["Close"], 20)
    d["SMA50"] = ta.trend.sma_indicator(d["Close"], 50)
    d["SMA200"] = ta.trend.sma_indicator(d["Close"], 200)

    # ==========================================================
# RSI identique au modèle Excel
# ==========================================================

def calculate_excel_rsi(close, period=14):

    variation = close.pct_change()

    gain = variation.clip(lower=0)
    loss = (-variation.clip(upper=0))

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


# ==========================================================
# Calcul des indicateurs
# ==========================================================

@st.cache_data
def prepare(df):

    d = df.copy()

    # Moyennes mobiles
    d["SMA20"] = ta.trend.sma_indicator(d["Close"], 20)
    d["SMA50"] = ta.trend.sma_indicator(d["Close"], 50)
    d["SMA200"] = ta.trend.sma_indicator(d["Close"], 200)

    # RSI identique au fichier Excel
    d["RSI"] = calculate_excel_rsi(d["Close"], 14)

    # MACD
    macd = ta.trend.MACD(d["Close"])

    d["MACD"] = macd.macd()
    d["SIGNAL"] = macd.macd_signal()
    d["HISTO"] = d["MACD"] - d["SIGNAL"]

    # Bollinger
    bb = ta.volatility.BollingerBands(
        d["Close"],
        window=20,
        window_dev=2
    )

    d["BB_UP"] = bb.bollinger_hband()
    d["BB_LOW"] = bb.bollinger_lband()

    return d

    macd = ta.trend.MACD(d["Close"])

    d["MACD"] = macd.macd()
    d["SIGNAL"] = macd.macd_signal()
    d["HISTO"] = d["MACD"] - d["SIGNAL"]

    bb = ta.volatility.BollingerBands(
        d["Close"],
        window=20,
        window_dev=2
    )

    d["BB_UP"] = bb.bollinger_hband()
    d["BB_LOW"] = bb.bollinger_lband()

    return d

# ==========================================================
# Import fichier
# ==========================================================

uploaded = st.file_uploader(
    "Importer Data_masi.xlsx",
    type=["xlsx"]
)

if uploaded:

    raw = load_data(uploaded)

    df = prepare(raw).dropna().reset_index(drop=True)

    last = df.iloc[-1]

    ref = raw[
        raw["Date"] <= pd.Timestamp(
            year=last["Date"].year - 1,
            month=12,
            day=31
        )
    ].iloc[-1]

    ytd = ((last["Close"] / ref["Close"]) - 1) * 100

    def perf(days):
        return (
            (
                last["Close"]
                /
                df.iloc[max(0, len(df) - days)]["Close"]
            ) - 1
        ) * 100 if len(df) > days else np.nan

    r1 = perf(21)
    r3 = perf(63)
    r6 = perf(126)
    r12 = perf(252)

    # ======================================================
    # Score
    # ======================================================

    score = 0

    score += 25 if last["Close"] > last["SMA200"] else 0
    score += 25 if last["SMA50"] > last["SMA200"] else 0
    score += 20 if last["SMA20"] > last["SMA50"] else 0
    score += 15 if last["MACD"] > last["SIGNAL"] else 0
    score += 15 if last["RSI"] > 60 else (
        10 if last["RSI"] > 40 else 5
    )

    reco = (
        "✅ ACHAT"
        if score >= 75
        else (
            "⚠️ SURVEILLER"
            if score >= 45
            else "❌ ATTENDRE"
        )
    )

    # ======================================================
    # Support / Résistance
    # ======================================================

    prices = raw["Close"].values

    mins = argrelextrema(
        prices,
        np.less,
        order=5
    )[0]

    maxs = argrelextrema(
        prices,
        np.greater,
        order=5
    )[0]

    support = (
        float(prices[mins][-1])
        if len(mins)
        else np.nan
    )

    resistance = (
        float(prices[maxs][-1])
        if len(maxs)
        else np.nan
    )

    # ======================================================
    # Onglets
    # ======================================================

    t1, t2, t3, t4, t5 = st.tabs(
        [
            "Dashboard",
            "Analyse",
            "Signaux",
            "Export",
            "Comité"
        ]
    )

    # ======================================================
    # DASHBOARD
    # ======================================================

    with t1:

        c = st.columns(5)

        c[0].metric("Cours", f"{last.Close:.2f}")
        c[1].metric("RSI", f"{last.RSI:.2f}")
        c[2].metric("Score", f"{score}/100")
        c[3].metric("YTD", f"{ytd:.2f}%")
        c[4].metric("Recommandation", reco)

        st.info(
            f"Référence YTD : "
            f"{ref['Date'].strftime('%d/%m/%Y')} | "
            f"{ref['Close']:.2f}"
        )

        k = st.columns(4)

        k[0].metric("1M", f"{r1:.2f}%")
        k[1].metric("3M", f"{r3:.2f}%")
        k[2].metric("6M", f"{r6:.2f}%")
        k[3].metric("1Y", f"{r12:.2f}%")

        st.write(f"Support : {support:.2f}")
        st.write(f"Résistance : {resistance:.2f}")

        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                gauge={
                    "axis": {
                        "range": [0, 100]
                    }
                }
            )
        )

        st.plotly_chart(
            gauge,
            use_container_width=True
        )

    # ======================================================
    # ANALYSE
    # ======================================================

    with t2:

        fig = go.Figure()

        for col in [
            "Close",
            "SMA20",
            "SMA50",
            "SMA200",
            "BB_UP",
            "BB_LOW"
        ]:

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

    # RSI

        r = go.Figure()

        r.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["RSI"],
                name="RSI"
            )
        )

        st.plotly_chart(
            r,
            use_container_width=True
        )

    # MACD

        m = go.Figure()

        m.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["HISTO"],
                name="Histogramme"
            )
        )

        m.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MACD"],
                name="MACD"
            )
        )

        m.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["SIGNAL"],
                name="Signal"
            )
        )

        st.plotly_chart(
            m,
            use_container_width=True
        )

    # ======================================================
    # SIGNAUX
    # ======================================================

    with t3:

        radar = go.Figure()

        radar.add_trace(
            go.Scatterpolar(
                r=[
                    score / 4,
                    25 if last["SMA50"] > last["SMA200"] else 0,
                    20 if last["SMA20"] > last["SMA50"] else 0,
                    15 if last["MACD"] > last["SIGNAL"] else 0,
                    max(5, min(15, last["RSI"] / 5))
                ],
                theta=[
                    "Prix",
                    "LT",
                    "MT",
                    "MACD",
                    "RSI"
                ],
                fill="toself"
            )
        )

        st.plotly_chart(
            radar,
            use_container_width=True
        )

    # ======================================================
    # EXPORT
    # ======================================================

    with t4:

        buf = BytesIO()

        with pd.ExcelWriter(
            buf,
            engine="openpyxl"
        ) as w:

            df.to_excel(
                w,
                sheet_name="Analyse",
                index=False
            )

            pd.DataFrame({
                "Date_ref": [ref["Date"]],
                "Cours_ref": [ref["Close"]],
                "YTD": [ytd],
                "Score": [score]
            }).to_excel(
                w,
                sheet_name="Dashboard",
                index=False
            )

        st.download_button(
            "Télécharger rapport",
            buf.getvalue(),
            "MASI_PRO_V7.xlsx"
        )

    # ======================================================
    # COMITE D'INVESTISSEMENT
    # ======================================================

    with t5:

        if score >= 80:
            conviction = "ÉLEVÉE"
            orientation = "CONSTRUCTIVE"
            feu = "🟢"

        elif score >= 60:
            conviction = "MODÉRÉE"
            orientation = "FAVORABLE"
            feu = "🟢"

        elif score >= 45:
            conviction = "PRUDENTE"
            orientation = "MITIGÉE"
            feu = "🟠"

        else:
            conviction = "FAIBLE"
            orientation = "DÉFENSIVE"
            feu = "🔴"

        st.subheader("Note destinée au Comité")

        commentaire = f"""
### Synthèse Exécutive

À la date du {last['Date'].strftime('%d/%m/%Y')}, l'indice MASI clôture à
{last['Close']:.2f} points et affiche une performance annuelle de
{ytd:.2f} %.

La tendance de fond demeure {'favorable' if last['Close'] > last['SMA200'] else 'moins favorable'},
le marché évoluant {'au-dessus' if last['Close'] > last['SMA200'] else 'en dessous'}
de sa moyenne mobile à 200 séances.

Le score MASI PRO ressort à {score}/100,
correspondant à un niveau de conviction :

{feu} {conviction}

Les indicateurs de momentum demeurent
{'favorablement orientés' if last['MACD'] > last['SIGNAL'] else 'plus mitigés'}.

Le RSI ressort à {last['RSI']:.2f}.

Les niveaux techniques à surveiller sont :

• Support : {support:.2f}

• Résistance : {resistance:.2f}

### Recommandation au Comité

L'évaluation globale demeure {orientation.lower()}.

{"Il est proposé de maintenir une exposition favorable au marché actions marocain et d'envisager un renforcement sélectif des positions." if score >= 80 else
"Il est proposé de conserver les positions actuelles tout en maintenant une vigilance sur les niveaux techniques clés." if score >= 60 else
"Une approche prudente est recommandée dans l'attente d'une amélioration des indicateurs techniques." if score >= 45 else
"Une posture défensive est recommandée jusqu'à l'apparition de signaux de marché plus favorables."}
"""

        st.markdown(commentaire)

        st.download_button(
            "📄 Télécharger la note Comité",
            commentaire,
            "Note_Comite_MASI.txt"
        )
