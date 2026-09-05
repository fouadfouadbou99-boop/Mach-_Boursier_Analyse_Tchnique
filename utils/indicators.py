import ta

def add_indicators(df):

    df["SMA20"] = ta.trend.sma_indicator(df["Close"], 20)

    df["SMA50"] = ta.trend.sma_indicator(df["Close"], 50)

    df["SMA200"] = ta.trend.sma_indicator(df["Close"], 200)

    df["RSI"] = ta.momentum.rsi(df["Close"], 14)

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    return df
st.write(df.tail(5)[[
    "Date",
    "Close",
    "RSI",
    "MACD",
    "MACD_SIGNAL"
]])
