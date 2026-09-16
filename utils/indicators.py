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
    # RSI
    # =====================================================

    df["RSI"] = ta.momentum.rsi(
        close=df["Close"],
        window=14
    )

    # =====================================================
    # MACD
    # =====================================================

    macd = ta.trend.MACD(
        close=df["Close"]
    )

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = (
        macd.macd_signal()
    )

    df["MACD_HIST"] = (
        df["MACD"]
        - df["MACD_SIGNAL"]
    )

    # =====================================================
    # BOLLINGER
    # =====================================================

    bb = ta.volatility.BollingerBands(
        close=df["Close"],
        window=20,
        window_dev=2
    )

    df["BB_UPPER"] = (
        bb.bollinger_hband()
    )

    df["BB_MIDDLE"] = (
        bb.bollinger_mavg()
    )

    df["BB_LOWER"] = (
        bb.bollinger_lband()
    )

    # =====================================================
    # VOLATILITE
    # =====================================================

    df["RET"] = np.log(
        df["Close"]
        / df["Close"].shift(1)
    )

    df["VOL20"] = (
        df["RET"]
        .rolling(20)
        .std()
        * np.sqrt(252)
    )

    # =====================================================
    # GOLDEN CROSS
    # =====================================================

    df["GOLDEN_CROSS"] = (
        (df["SMA50"] > df["SMA200"])
        &
        (
            df["SMA50"].shift(1)
            <= df["SMA200"].shift(1)
        )
    )

    df["DEATH_CROSS"] = (
        (df["SMA50"] < df["SMA200"])
        &
        (
            df["SMA50"].shift(1)
            >= df["SMA200"].shift(1)
        )
    )

    # =====================================================
    # MACD CROSS
    # =====================================================

    df["MACD_BULL"] = (
        (df["MACD"] > df["MACD_SIGNAL"])
        &
        (
            df["MACD"].shift(1)
            <= df["MACD_SIGNAL"].shift(1)
        )
    )

    df["MACD_BEAR"] = (
        (df["MACD"] < df["MACD_SIGNAL"])
        &
        (
            df["MACD"].shift(1)
            >= df["MACD_SIGNAL"].shift(1)
        )
    )

    return df
