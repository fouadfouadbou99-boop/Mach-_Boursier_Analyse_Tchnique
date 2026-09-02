import streamlit as st
import pandas as pd
from utils.indicators import add_indicators
from utils.patterns import detect_support_resistance
from utils.charts import plot_chart

st.set_page_config(layout="wide")

st.title("Analyse Chartiste MASI")

file = "data/Data_masi.xlsx"

df = pd.read_excel(file)

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values("Date")

df = add_indicators(df)

supports, resistances = detect_support_resistance(df)

fig = plot_chart(df, supports, resistances)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(df.tail(20))
