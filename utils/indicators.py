import pandas as pd
import numpy as np
import ta


def add_indicators(df):

    # =====================================================
    # MOYENNES MOBILES
    # =====================================================

    df["SMA20"] = ta.trend.sma_indicator(
        df["Close"],
        window=20
    )

    df["SMA50"] = ta.trend.sma_indicator(
        df["Close"],
        window=50
    )

    df["SMA200"] = ta.trend.sma_indicator(
        df["Close"],
        window=200
    )

    # =====================================================
    # PREPARATION RSI
    # =====================================================

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    # =====================================================
    # RSI TA
    # =====================================================

    df["RSI_TA"] = ta.momentum.rsi(
        close=df["Close"],
        window=14
    )

    # =====================================================
    # RSI WILDER
    # =====================================================

    avg_gain_wilder = gain.ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    avg_loss_wilder = loss.ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    rs_wilder = avg_gain_wilder / avg_loss_wilder

    df["RSI_WILDER"] = (
        100 - (100 / (1 + rs_wilder))
    )

    # =====================================================
    # RSI SMA
    # =====================================================

    avg_gain_sma = gain.rolling(
        window=14
    ).mean()

    avg_loss_sma = loss.rolling(
        window=14
    ).mean()

    rs_sma = avg_gain_sma / avg_loss_sma

    df["RSI_SMA"] = (
        100 - (100 / (1 + rs_sma))
    )

    # =====================================================
    # CHOIX DU RSI UTILISE
    # =====================================================

    # 1 = RSI bibliothèque ta
    # df["RSI"] = df["RSI_TA"]

    # 2 = RSI Wilder
    df["RSI"] = df["RSI_WILDER"]

    # 3 = RSI SMA
    # df["RSI"] = df["RSI_SMA"]

    # =====================================================
    # MACD
    # =====================================================

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    df["MACD_HIST"] = (
        df["MACD"]
        - df["MACD_SIGNAL"]
    )

    return df
    st.subheader("Comparaison des RSI")

st.dataframe(
    df[
        [
            "Date",
            "Close",
            "RSI_TA",
            "RSI_WILDER",
            "RSI_SMA"
        ]
    ].tail(10),
    use_container_width=True
)

st.write(
    "RSI_TA :",
    round(df["RSI_TA"].iloc[-1], 2)
)

st.write(
    "RSI_WILDER :",
    round(df["RSI_WILDER"].iloc[-1], 2)
)

st.write(
    "RSI_SMA :",
    round(df["RSI_SMA"].iloc[-1], 2)
)
