import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from io import BytesIO
from scipy.signal import argrelextrema

st.set_page_config(page_title="MASI PRO V5", page_icon="📈", layout="wide")

st.markdown("""<h1 style='text-align:center;color:#0E4D92;'>📈 MASI PRO V5</h1>
<p style='text-align:center;'>Plateforme professionnelle d'analyse technique du MASI</p>""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name='Data_masi', engine='openpyxl')
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    return df.dropna(subset=['Date','Close']).sort_values('Date').reset_index(drop=True)


def add_indicators(df):
    df['SMA20']=ta.trend.sma_indicator(df['Close'],20)
    df['SMA50']=ta.trend.sma_indicator(df['Close'],50)
    df['SMA200']=ta.trend.sma_indicator(df['Close'],200)
    df['RSI']=ta.momentum.rsi(df['Close'],14)
    m=ta.trend.MACD(df['Close'])
    df['MACD']=m.macd()
    df['SIGNAL']=m.macd_signal()
    df['HISTO']=df['MACD']-df['SIGNAL']
    bb=ta.volatility.BollingerBands(df['Close'],20,2)
    df['BB_UP']=bb.bollinger_hband()
    df['BB_LOW']=bb.bollinger_lband()
    return df


def detect_sr(df):
    prices=df['Close'].values
    mins=argrelextrema(prices,np.less,order=5)[0]
    maxs=argrelextrema(prices,np.greater,order=5)[0]
    return prices[mins], prices[maxs]


def score(df):
    s=0
    last=df.iloc[-1]
    if last['Close']>last['SMA200']: s+=25
    if last['SMA50']>last['SMA200']: s+=25
    if last['SMA20']>last['SMA50']: s+=20
    if last['MACD']>last['SIGNAL']: s+=15
    if 45<=last['RSI']<=70: s+=15
    return min(s,100)


def trend(last):
    if last['Close']>last['SMA200'] and last['SMA50']>last['SMA200']:
        return '🟢 Tendance Haussière'
    elif last['Close']<last['SMA200']:
        return '🔴 Tendance Baissière'
    return '🟡 Consolidation'

uploaded_file=st.file_uploader('Importer Data_masi.xlsx',type=['xlsx'])

if uploaded_file:
    df=add_indicators(load_data(uploaded_file)).dropna()
    last=df.iloc[-1]
    sc=score(df)
    supports,resistances=detect_sr(df)
    ytd=((last['Close']/df['Close'].iloc[0])-1)*100

    reco='✅ ACHAT' if sc>=80 else ('⚠️ SURVEILLER' if sc>=60 else '❌ ATTENDRE')

    t1,t2,t3,t4=st.tabs(['📊 Dashboard','📈 Analyse','🎯 Signaux','📥 Export'])

    with t1:
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric('Cours',f"{last['Close']:.2f}")
        c2.metric('RSI',f"{last['RSI']:.2f}")
        c3.metric('Score',f'{sc}/100')
        c4.metric('Perf YTD',f'{ytd:.2f}%')
        c5.metric('Recommandation',reco)
        st.info(trend(last))

        resume=pd.DataFrame({
        'Indicateur':['Close','SMA20','SMA50','SMA200','RSI','MACD'],
        'Valeur':[last['Close'],last['SMA20'],last['SMA50'],last['SMA200'],last['RSI'],last['MACD']]})
        st.dataframe(resume,use_container_width=True)

    with t2:
        fig=go.Figure()
        for col in ['Close','SMA20','SMA50','SMA200']:
            fig.add_trace(go.Scatter(x=df['Date'],y=df[col],name=col))
        fig.add_trace(go.Scatter(x=df['Date'],y=df['BB_UP'],name='BB Haut'))
        fig.add_trace(go.Scatter(x=df['Date'],y=df['BB_LOW'],name='BB Bas'))

        for s in supports[-5:]: fig.add_hline(y=float(s),line_dash='dot',line_color='green')
        for r in resistances[-5:]: fig.add_hline(y=float(r),line_dash='dot',line_color='red')
        fig.update_layout(height=650,title='MASI & Moyennes Mobiles')
        st.plotly_chart(fig,use_container_width=True)

        rsi=go.Figure()
        rsi.add_trace(go.Scatter(x=df['Date'],y=df['RSI'],name='RSI'))
        rsi.add_hline(y=70,line_color='red')
        rsi.add_hline(y=30,line_color='green')
        st.plotly_chart(rsi,use_container_width=True)

        macd=go.Figure()
        macd.add_trace(go.Scatter(x=df['Date'],y=df['MACD'],name='MACD'))
        macd.add_trace(go.Scatter(x=df['Date'],y=df['SIGNAL'],name='Signal'))
        st.plotly_chart(macd,use_container_width=True)

    with t3:
        signal='⚪ NEUTRE'
        if last['MACD']>last['SIGNAL'] and last['RSI']>50 and last['Close']>last['SMA50']:
            signal='🟢 ACHAT'
        elif last['MACD']<last['SIGNAL'] and last['RSI']<50:
            signal='🔴 VENTE'
        st.success(signal)

        radar=go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=[25 if last['Close']>last['SMA200'] else 0,25 if last['SMA50']>last['SMA200'] else 0,20 if last['SMA20']>last['SMA50'] else 0,15 if last['MACD']>last['SIGNAL'] else 0,15 if 45<=last['RSI']<=70 else 0],
            theta=['Prix','SMA50','SMA20','MACD','RSI'],fill='toself'))
        st.plotly_chart(radar,use_container_width=True)

    with t4:
        buffer=BytesIO()
        with pd.ExcelWriter(buffer,engine='openpyxl') as writer:
            df.to_excel(writer,sheet_name='Analyse',index=False)
            pd.DataFrame({'Date':[last['Date']],'Close':[last['Close']],'RSI':[last['RSI']],'Score':[sc],'Recommandation':[reco],'Tendance':[trend(last)]}).to_excel(writer,sheet_name='Dashboard',index=False)
        st.download_button('📥 Télécharger MASI PRO V5',buffer.getvalue(),'MASI_PRO_V5.xlsx')
