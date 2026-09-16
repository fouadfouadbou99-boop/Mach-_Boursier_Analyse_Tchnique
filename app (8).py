import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from io import BytesIO
from scipy.signal import argrelextrema

st.set_page_config(page_title='MASI Pro V4', page_icon='📈', layout='wide')
st.title('📈 MASI Pro V4')

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name='Data_masi')
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    return df.dropna().sort_values('Date').reset_index(drop=True)

def add_indicators(df):
    df['SMA20']=ta.trend.sma_indicator(df['Close'],20)
    df['SMA50']=ta.trend.sma_indicator(df['Close'],50)
    df['SMA200']=ta.trend.sma_indicator(df['Close'],200)
    df['RSI']=ta.momentum.rsi(df['Close'],14)
    macd=ta.trend.MACD(df['Close'])
    df['MACD']=macd.macd()
    df['SIGNAL']=macd.macd_signal()
    df['HISTO']=df['MACD']-df['SIGNAL']
    bb=ta.volatility.BollingerBands(df['Close'],20,2)
    df['BB_UP']=bb.bollinger_hband()
    df['BB_LOW']=bb.bollinger_lband()
    df['RET']=np.log(df['Close']/df['Close'].shift(1))
    df['VOL20']=df['RET'].rolling(20).std()*np.sqrt(252)
    return df

def detect_sr(df):
    p=df['Close'].values
    s=p[argrelextrema(p,np.less,order=5)[0]]
    r=p[argrelextrema(p,np.greater,order=5)[0]]
    return s,r

def run_backtest(df):
    buy=((df['SMA20']>df['SMA50'])&(df['MACD']>df['SIGNAL'])&(df['RSI']>50))
    sell=((df['SMA20']<df['SMA50'])|(df['MACD']<df['SIGNAL'])|(df['RSI']<45))
    position=0
    entry=0
    trades=[]
    for i in range(len(df)):
        price=df['Close'].iloc[i]
        if position==0 and buy.iloc[i]:
            position=1
            entry=price
        elif position==1 and sell.iloc[i]:
            perf=((price-entry)/entry)*100
            trades.append(perf)
            position=0
    return trades

uploaded=st.file_uploader('Importer Excel',type=['xlsx'])
if uploaded:
    df=load_data(uploaded)
    df=add_indicators(df).dropna()
    last=df.iloc[-1]
    st.metric('Cours',round(last['Close'],2))
    fig=go.Figure()
    for col in ['Close','SMA20','SMA50','SMA200']:
        fig.add_trace(go.Scatter(x=df['Date'],y=df[col],name=col))
    st.plotly_chart(fig,use_container_width=True)
    trades=run_backtest(df)
    if trades:
        st.write(f'Win Rate: {np.mean(np.array(trades)>0)*100:.1f}%')
        st.write(f'Performance: {sum(trades):.2f}%')
    buffer=BytesIO()
    with pd.ExcelWriter(buffer,engine='openpyxl') as writer:
        df.to_excel(writer,index=False)
    st.download_button('Télécharger',buffer.getvalue(),'MASI_PRO_V4.xlsx')
