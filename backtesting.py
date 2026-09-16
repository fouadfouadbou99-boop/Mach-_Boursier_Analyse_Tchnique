import pandas as pd
import numpy as np


def backtest_strategy(df):

    data = df.copy()

    data["BUY"] = (
        (data["SMA20"] > data["SMA50"])
        &
        (data["MACD"] > data["MACD_SIGNAL"])
        &
        (data["RSI"] > 50)
    )

    data["SELL"] = (
        (data["SMA20"] < data["SMA50"])
        |
        (data["MACD"] < data["MACD_SIGNAL"])
        |
        (data["RSI"] < 45)
    )

    capital = 100

    position = 0

    entry_price = 0

    trades = []

    equity = [capital]

    for i in range(len(data)):

        price = data["Close"].iloc[i]

        if (
            position == 0
            and data["BUY"].iloc[i]
        ):
            position = 1
            entry_price = price

        elif (
            position == 1
            and data["SELL"].iloc[i]
        ):

            perf = (
                price - entry_price
            ) / entry_price

            capital *= (
                1 + perf
            )

            trades.append(
                perf * 100
            )

            position = 0

        equity.append(capital)

    equity = pd.Series(equity)

    drawdown = (
        equity - equity.cummax()
    ) / equity.cummax()

    return {
        "nb_trades": len(trades),
        "winrate": (
            np.mean(
                np.array(trades) > 0
            ) * 100
            if trades
            else 0
        ),
        "performance": (
            capital - 100
        ),
        "max_drawdown": (
            drawdown.min() * 100
        ),
        "equity": equity
    }
