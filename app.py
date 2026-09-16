import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from scipy.signal import argrelextrema

st.set_page_config(page_title="Analyse Technique MASI Pro", page_icon="📈", layout="wide")
st.title("📈 Analyse Technique MASI Pro")

uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx"])


def filtrer_niveaux(levels, seuil=0.01):
    niveaux = []
    for lvl in sorted(levels):
        if not niveaux:
            niveaux.append(float(lvl))
        elif abs(lvl - niveaux[-1]) / niveaux[-1] > seuil:
            niveaux.append(float(lvl))
    return niveaux

if uploaded_file:
    try:
        try:
            df = pd.read_excel(uploaded_file, sheet_name="Data_masi")
        except Exception:
            df = pd.read_excel(uploaded_file)

        df.columns = df.columns.str.strip()

        if 'Date' not in df.columns or 'Close' not in df.columns:
            st.error('Colonnes Date et Close obligatoires')
            st.stop()

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        df['Close'] = (
            df['Close'].astype(str)
            .str.replace('\xa0','', regex=False)
            .str.replace(' ','', regex=False)
            .str.replace(',', '.', regex=False)
        )

        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')

        df = df.dropna(subset=['Date','Close'])
        df = df.sort_values('Date').reset_index(drop=True)

        df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)

        if len(df) >= 200:
            df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
        else:
            df['SMA200'] = np.nan

        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD'] = macd_obj.macd()
        df['SIGNAL'] = macd_obj.macd_signal()
        df['HISTO'] = df['MACD'] - df['SIGNAL']

        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_HAUT'] = bb.bollinger_hband()
        df['BB_BAS'] = bb.bollinger_lband()
        df['BB_MILIEU'] = bb.bollinger_mavg()

        df['Rendement'] = np.log(df['Close'] / df['Close'].shift(1))
        df['Vol20'] = df['Rendement'].rolling(20).std() * np.sqrt(252)
        df['PlusHaut20'] = df['Close'].rolling(20).max()
        df['PlusBas20'] = df['Close'].rolling(20).min()

        prices = df['Close'].values
        minima = argrelextrema(prices, np.less, order=5)[0]
        maxima = argrelextrema(prices, np.greater, order=5)[0]

        supports = filtrer_niveaux(prices[minima])
        resistances = filtrer_niveaux(prices[maxima])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Cours'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA20'], name='SMA20'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA50'], name='SMA50'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA200'], name='SMA200'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_HAUT'], name='BB Haut'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_BAS'], name='BB Bas'))

        for s in supports[-5:]:
            fig.add_hline(y=s, line_color='green', line_dash='dot')
        for r in resistances[-5:]:
            fig.add_hline(y=r, line_color='red', line_dash='dash')

        st.plotly_chart(fig, use_container_width=True)

        close = df['Close'].iloc[-1]
        sma20 = df['SMA20'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        sma200 = df['SMA200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        signal = df['SIGNAL'].iloc[-1]
        histo = df['HISTO'].iloc[-1]
        vol20 = df['Vol20'].iloc[-1]
        ph20 = df['PlusHaut20'].iloc[-1]
        pb20 = df['PlusBas20'].iloc[-1]

        score = 0
        if not np.isnan(sma200):
            if close > sma200: score += 15
            if sma50 > sma200: score += 15
        if sma20 > sma50: score += 10
        if macd > signal: score += 10
        if histo > 0: score += 10

        if 45 <= rsi <= 65: score += 15
        elif 35 <= rsi < 45 or 65 < rsi <= 75: score += 10
        elif 25 <= rsi < 35: score += 5

        position = np.nan
        if ph20 != pb20:
            position = ((close - pb20)/(ph20-pb20))*100
            if position > 70: score += 15
            elif position > 50: score += 10
            elif position > 30: score += 5

        if vol20 < 0.15: score += 10
        elif vol20 < 0.25: score += 5

        st.header('🎯 Score Technique')
        c1,c2,c3 = st.columns(3)
        c1.metric('Score', f'{score}/100')
        c2.metric('RSI', f'{rsi:.1f}')
        c3.metric('Range20', f'{position:.0f}%')

        if score >= 80:
            st.success('ACHAT FORT')
        elif score >= 65:
            st.success('ACHAT')
        elif score >= 50:
            st.info('CONSERVATION')
        elif score >= 35:
            st.warning('VIGILANCE')
        else:
            st.error('VENTE')

        st.dataframe(df.tail(50), use_container_width=True)

    except Exception as e:
        st.exception(e)
