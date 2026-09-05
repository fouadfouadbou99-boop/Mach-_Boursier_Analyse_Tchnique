import ta
import numpy as np

def add_indicators(df):

    # ==========================
    # MOYENNES MOBILES
    # ==========================

    df["SMA20"] = ta.trend.sma_indicator(df["Close"], 20)

    df["SMA50"] = ta.trend.sma_indicator(df["Close"], 50)

    df["SMA200"] = ta.trend.sma_indicator(df["Close"], 200)

    # ==========================
    # RSI WILDER (COMME EXCEL)
    # ==========================

    delta = df["Close"].diff()

    df["Gain"] = np.where(delta > 0, delta, 0)

    df["Perte"] = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(df["Gain"]).ewm(
        alpha=1/14,
        adjust=False
    ).mean()

    avg_loss = pd.Series(df["Perte"]).ewm(
        alpha=1/14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = np.where(
        (avg_gain == 0) & (avg_loss == 0),
        50,
        np.where(
            avg_loss == 0,
            100,
            np.where(
                avg_gain == 0,
                0,
                100 - (100 / (1 + rs))
            )
        )
    )

    # ==========================
    # MACD
    # ==========================

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    df["MACD_HIST"] = (
        df["MACD"]
        - df["MACD_SIGNAL"]
    )

    return df
