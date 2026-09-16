import numpy as np
from scipy.signal import argrelextrema


def detect_support_resistance(df):

    prices = df["Close"].values

    minima = argrelextrema(
        prices,
        np.less,
        order=5
    )[0]

    maxima = argrelextrema(
        prices,
        np.greater,
        order=5
    )[0]

    supports = prices[minima]

    resistances = prices[maxima]

    return supports, resistances


def detect_double_top(df):

    highs = argrelextrema(
        df["Close"].values,
        np.greater,
        order=5
    )[0]

    if len(highs) < 2:
        return False

    h1 = df["Close"].iloc[highs[-1]]
    h2 = df["Close"].iloc[highs[-2]]

    return abs(h1 - h2) / h1 < 0.02


def detect_double_bottom(df):

    lows = argrelextrema(
        df["Close"].values,
        np.less,
        order=5
    )[0]

    if len(lows) < 2:
        return False

    l1 = df["Close"].iloc[lows[-1]]
    l2 = df["Close"].iloc[lows[-2]]

    return abs(l1 - l2) / l1 < 0.02
