# MASI PRO V7
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from scipy.signal import argrelextrema
import ta

st.set_page_config(page_title="MASI PRO V7", page_icon="📈", layout="wide")
st.title("📈 MASI PRO V7")

@st.cache_data
def load_data(file):
    df=pd.read_excel(file,sheet_name='Data_masi',engine='openpyxl')
    df.columns=df.columns.str.strip()
    df['Date']=pd.to_datetime(df['Date'])
    df['Close']=pd.to_numeric(df['Close'])
    return df.sort_values('Date').reset_index(drop=True)

@st.cache_data
def prepare(df):
    d=df.copy()
    d['SMA20']=ta.trend.sma_indicator(d['Close'],20)
    d['SMA50']=ta.trend.sma_indicator(d['Close'],50)
    d['SMA200']=ta.trend.sma_indicator(d['Close'],200)
    d['RSI']=ta.momentum.rsi(d['Close'],14)
    m=ta.trend.MACD(d['Close'])
    d['MACD']=m.macd(); d['SIGNAL']=m.macd_signal(); d['HISTO']=d['MACD']-d['SIGNAL']
    bb=ta.volatility.BollingerBands(d['Close'],20,2)
    d['BB_UP']=bb.bollinger_hband(); d['BB_LOW']=bb.bollinger_lband()
    return d

uploaded=st.file_uploader('Importer Data_masi.xlsx',type=['xlsx'])
if uploaded:
    raw=load_data(uploaded)
    df=prepare(raw).dropna().reset_index(drop=True)
    last=df.iloc[-1]

    ref=raw[raw['Date']<=pd.Timestamp(year=last['Date'].year-1,month=12,day=31)].iloc[-1]
    ytd=((last['Close']/ref['Close'])-1)*100

    def perf(days):
      return ((last['Close']/df.iloc[max(0,len(df)-days)]['Close'])-1)*100 if len(df)>days else np.nan

    r1,r3,r6,r12=perf(21),perf(63),perf(126),perf(252)

    score=0
    score+=25 if last['Close']>last['SMA200'] else 0
    score+=25 if last['SMA50']>last['SMA200'] else 0
    score+=20 if last['SMA20']>last['SMA50'] else 0
    score+=15 if last['MACD']>last['SIGNAL'] else 0
    score+=15 if last['RSI']>60 else (10 if last['RSI']>40 else 5)

    reco='✅ ACHAT' if score>=75 else ('⚠️ SURVEILLER' if score>=45 else '❌ ATTENDRE')

    prices=raw['Close'].values
    mins=argrelextrema(prices,np.less,order=5)[0]
    maxs=argrelextrema(prices,np.greater,order=5)[0]
    support=float(prices[mins][-1]) if len(mins) else np.nan
    resistance=float(prices[maxs][-1]) if len(maxs) else np.nan

    t1,t2,t3,t4=st.tabs(['Dashboard','Analyse','Signaux','Export'])

    with t1:
      c=st.columns(5)
      c[0].metric('Cours',f'{last.Close:.2f}')
      c[1].metric('RSI',f'{last.RSI:.2f}')
      c[2].metric('Score',f'{score}/100')
      c[3].metric('YTD',f'{ytd:.2f}%')
      c[4].metric('Reco',reco)
      st.info(f"Référence YTD : {ref['Date'].strftime('%d/%m/%Y')} | {ref['Close']:.2f}")
      k=st.columns(4)
      k[0].metric('1M',f'{r1:.2f}%')
      k[1].metric('3M',f'{r3:.2f}%')
      k[2].metric('6M',f'{r6:.2f}%')
      k[3].metric('1Y',f'{r12:.2f}%')
      st.write(f'Support : {support:.2f}')
      st.write(f'Résistance : {resistance:.2f}')
      gauge=go.Figure(go.Indicator(mode='gauge+number',value=score,gauge={'axis':{'range':[0,100]}}))
      st.plotly_chart(gauge,use_container_width=True)

    with t2:
      fig=go.Figure()
      for col in ['Close','SMA20','SMA50','SMA200','BB_UP','BB_LOW']:
        fig.add_trace(go.Scatter(x=df['Date'],y=df[col],name=col))
      st.plotly_chart(fig,use_container_width=True)
      r=go.Figure(); r.add_trace(go.Scatter(x=df['Date'],y=df['RSI'],name='RSI')); st.plotly_chart(r,use_container_width=True)
      m=go.Figure(); m.add_trace(go.Bar(x=df['Date'],y=df['HISTO'],name='Histo')); m.add_trace(go.Scatter(x=df['Date'],y=df['MACD'],name='MACD')); m.add_trace(go.Scatter(x=df['Date'],y=df['SIGNAL'],name='Signal')); st.plotly_chart(m,use_container_width=True)

    with t3:
      radar=go.Figure(); radar.add_trace(go.Scatterpolar(r=[score/4,25 if last['SMA50']>last['SMA200'] else 0,20 if last['SMA20']>last['SMA50'] else 0,15 if last['MACD']>last['SIGNAL'] else 0,max(5,min(15,last['RSI']/5))],theta=['Prix','LT','MT','MACD','RSI'],fill='toself'))
      st.plotly_chart(radar,use_container_width=True)
      st.dataframe(pd.DataFrame({'Indicateur':['Close','SMA20','SMA50','SMA200','RSI','MACD','SIGNAL','HISTO'],'Valeur':[last['Close'],last['SMA20'],last['SMA50'],last['SMA200'],last['RSI'],last['MACD'],last['SIGNAL'],last['HISTO']]}))

    with t4:
      buf=BytesIO()
      with pd.ExcelWriter(buf,engine='openpyxl') as w:
        df.to_excel(w,sheet_name='Analyse',index=False)
        pd.DataFrame({'Date_ref':[ref['Date']],'Cours_ref':[ref['Close']],'YTD':[ytd],'Score':[score]}).to_excel(w,sheet_name='Dashboard',index=False)
      st.download_button('Télécharger rapport',buf.getvalue(),'MASI_PRO_V7.xlsx')
