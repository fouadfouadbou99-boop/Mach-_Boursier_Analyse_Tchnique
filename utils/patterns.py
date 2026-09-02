import numpy as np
from scipy.signal import argrelextrema

def detect_support_resistance(df):

    prices = df["Close"].values

    support_idx = argrelextrema(prices, np.less, order=5)[0]

    resistance_idx = argrelextrema(prices, np.greater, order=5)[0]

    supports = prices[support_idx]

    resistances = prices[resistance_idx]

    return supports, resistances
