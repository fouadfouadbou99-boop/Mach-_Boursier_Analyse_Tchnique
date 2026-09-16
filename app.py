# MASI PRO V6
# Version complète professionnelle
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from io import BytesIO
from scipy.signal import argrelextrema

st.set_page_config(page_title="MASI PRO V6", page_icon="📈", layout="wide")
st.title("📈 MASI PRO V6")

@st.cache_data
def load_data(file):
    df=pd.read_excel(file,sheet_name='Data_masi',engine='openpyxl')
    df.columns=df.columns.str.strip()
    df['Date']=pd.to_datetime(df['Date'],errors='coerce')
    df['Close']=pd.to_numeric(df['Close'],errors='coerce')
    return df.dropna(subset=['Date','Close']).sort_values('Date').reset_index(drop=True)

def add_indicators(df):
    df['SMA20']=ta.trend.sma_indicator(df['Close'],20)
    df['SMA50']=ta.trend.sma_indicator(df['Close'],50)
    df['SMA200']=ta.trend.sma_indicator(df['Close'],200)
    df['RSI']=ta.momentum.rsi(df['Close'],14)
    macd=ta.trend.MACD(df['Close'])
    df['MACD']=macd.macd(); df['SIGNAL']=macd.macd_signal(); df['HISTO']=df['MACD']-df['SIGNAL']
    bb=ta.volatility.BollingerBands(df['Close'],20,2)
    df['BB_UP']=bb.bollinger_hband(); df['BB_LOW']=bb.bollinger_lband()
    return df

def detect_sr(df):
    p=df['Close'].values
    return p[argrelextrema(p,np.less,order=5)[0]], p[argrelextrema(p,np.greater,order=5)[0]]

def score(last):
    s=0
    if last['Close']>last['SMA200']: s+=25
    if last['SMA50']>last['SMA200']: s+=25
    if last['SMA20']>last['SMA50']: s+=20
    if last['MACD']>last['SIGNAL']: s+=15
    if last['RSI']>60: s+=15
    elif last['RSI']>40: s+=10
    elif last['RSI']>30: s+=5
    return min(s,100)

up=st.file_uploader('Importer Data_masi.xlsx',type=['xlsx'])
if up:
    df=add_indicators(load_data(up)).dropna()
    last=df.iloc[-1]
    sc=score(last)
    sup,res=detect_sr(df)

    year=last['Date'].year
    fy=df[df['Date'].dt.year==year].iloc[0]['Close']
    ytd=((last['Close']/fy)-1)*100

    def perf(days):
        if len(df)>days:
            return ((last['Close']/df.iloc[-days]['Close'])-1)*100
        return np.nan

    p1=perf(21); p3=perf(63); p6=perf(126); p12=perf(252)

    if last['Close']>last['SMA200']: trend='🟢 Haussier LT'
    elif last['Close']>last['SMA50']: trend='🟡 Correction'
    else: trend='🔴 Baissier'

    reco='✅ ACHAT' if sc>=75 else ('⚠️ SURVEILLER' if sc>=45 else '❌ ATTENDRE')

    t1,t2,t3,t4=st.tabs(['Dashboard','Analyse','Signaux','Export'])

    with t1:
        c=st.columns(5)
        c[0].metric('Cours',round(last['Close'],2))
        c[1].metric('RSI',round(last['RSI'],2))
        c[2].metric('Score',f'{sc}/100')
        c[3].metric('Perf YTD',f'{ytd:.2f}%')
        c[4].metric('Reco',reco)
        st.info(trend)

        k=st.columns(4)
        k[0].metric('1 Mois',f'{p1:.2f}%')
        k[1].metric('3 Mois',f'{p3:.2f}%')
        k[2].metric('6 Mois',f'{p6:.2f}%')
        k[3].metric('1 An',f'{p12:.2f}%')

        dist=((last['Close']/last['SMA200'])-1)*100
        st.write(f'Distance SMA200 : {dist:.2f}%')
        st.write(f'Support majeur : {float(sup[-1]) if len(sup) else "N/A"}')
        st.write(f'Résistance majeure : {float(res[-1]) if len(res) else "N/A"}')

    with t2:
        fig=go.Figure()
        for x in ['Close','SMA20','SMA50','SMA200']:
            fig.add_trace(go.Scatter(x=df.Date,y=df[x],name=x))
        fig.add_trace(go.Scatter(x=df.Date,y=df.BB_UP,name='BB Haut'))
        fig.add_trace(go.Scatter(x=df.Date,y=df.BB_LOW,name='BB Bas'))
        st.plotly_chart(fig,use_container_width=True)

        rsi=go.Figure(); rsi.add_trace(go.Scatter(x=df.Date,y=df.RSI,name='RSI')); st.plotly_chart(rsi,use_container_width=True)
        mac=go.Figure(); mac.add_trace(go.Scatter(x=df.Date,y=df.MACD,name='MACD')); mac.add_trace(go.Scatter(x=df.Date,y=df.SIGNAL,name='Signal')); st.plotly_chart(mac,use_container_width=True)

    with t3:
        radar=go.Figure()
        radar.add_trace(go.Scatterpolar(r=[25 if last['Close']>last['SMA200'] else 0,25 if last['SMA50']>last['SMA200'] else 0,20 if last['SMA20']>last['SMA50'] else 0,15 if last['MACD']>last['SIGNAL'] else 0,15 if last['RSI']>60 else 5],theta=['Prix','SMA50','SMA20','MACD','RSI'],fill='toself'))
        st.plotly_chart(radar,use_container_width=True)
        st.dataframe(pd.DataFrame({'Indicateur':['Close','SMA20','SMA50','SMA200','RSI','MACD','SIGNAL','HISTO'],'Valeur':[last['Close'],last['SMA20'],last['SMA50'],last['SMA200'],last['RSI'],last['MACD'],last['SIGNAL'],last['HISTO']]}))

    with t4:
        buf=BytesIO()
        with pd.ExcelWriter(buf,engine='openpyxl') as w:
            df.to_excel(w,sheet_name='Analyse',index=False)
        st.download_button('Télécharger V6',buf.getvalue(),'MASI_PRO_V6.xlsx')
