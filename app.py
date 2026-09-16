# MASI PRO V5.1 - Corrections
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from io import BytesIO
from scipy.signal import argrelextrema

st.set_page_config(page_title="MASI PRO V5.1",page_icon="📈",layout="wide")
st.title("📈 MASI PRO V5.1")

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
    m=ta.trend.MACD(df['Close'])
    df['MACD']=m.macd()
    df['SIGNAL']=m.macd_signal()
    df['HISTO']=df['MACD']-df['SIGNAL']
    bb=ta.volatility.BollingerBands(df['Close'],20,2)
    df['BB_UP']=bb.bollinger_hband(); df['BB_LOW']=bb.bollinger_lband()
    return df

def detect_sr(df):
    p=df['Close'].values
    return p[argrelextrema(p,np.less,order=5)[0]], p[argrelextrema(p,np.greater,order=5)[0]]

def calculate_score(df):
    last=df.iloc[-1]; s=0
    if last['Close']>last['SMA200']: s+=25
    if last['SMA50']>last['SMA200']: s+=25
    if last['SMA20']>last['SMA50']: s+=20
    if last['MACD']>last['SIGNAL']: s+=15
    r=last['RSI']
    if r>60: s+=15
    elif r>40: s+=10
    elif r>30: s+=5
    return min(s,100)

def analyse_trend(last):
    if last['Close']>last['SMA200']:
        return '🟢 Haussier long terme'
    elif last['Close']>last['SMA50']:
        return '🟡 Correction dans tendance positive'
    return '🔴 Baissier'

up=st.file_uploader('Importer Data_masi.xlsx',type=['xlsx'])
if up:
    df=add_indicators(load_data(up)).dropna()
    last=df.iloc[-1]
    score=calculate_score(df)
    supports,resistances=detect_sr(df)

    current_year=last['Date'].year
    df_ytd=df[df['Date'].dt.year==current_year]
    first_close=df_ytd.iloc[0]['Close']
    ytd=((last['Close']/first_close)-1)*100

    if score>=75: reco='✅ ACHAT'
    elif score>=45: reco='⚠️ SURVEILLER'
    else: reco='❌ ATTENDRE'

    t1,t2,t3,t4=st.tabs(['Dashboard','Analyse','Signaux','Export'])
    with t1:
        a,b,c,d,e=st.columns(5)
        a.metric('Cours',f'{last.Close:.2f}')
        b.metric('RSI',f'{last.RSI:.2f}')
        c.metric('Score',f'{score}/100')
        d.metric('Perf YTD',f'{ytd:.2f}%')
        e.metric('Recommandation',reco)
        st.info(analyse_trend(last))
        st.dataframe(pd.DataFrame({'Indicateur':['Close','SMA20','SMA50','SMA200','RSI','MACD','Signal','Histogramme'],'Valeur':[last['Close'],last['SMA20'],last['SMA50'],last['SMA200'],last['RSI'],last['MACD'],last['SIGNAL'],last['HISTO']]}),use_container_width=True)
    with t2:
        fig=go.Figure()
        for col in ['Close','SMA20','SMA50','SMA200']:
            fig.add_trace(go.Scatter(x=df['Date'],y=df[col],name=col))
        for s in supports[-5:]: fig.add_hline(y=float(s),line_dash='dot',line_color='green')
        for r in resistances[-5:]: fig.add_hline(y=float(r),line_dash='dot',line_color='red')
        st.plotly_chart(fig,use_container_width=True)
    with t3:
        st.success(reco)
    with t4:
        buf=BytesIO()
        with pd.ExcelWriter(buf,engine='openpyxl') as w:
            df.to_excel(w,index=False,sheet_name='Analyse')
        st.download_button('Télécharger',buf.getvalue(),'MASI_PRO_V5_1.xlsx')
