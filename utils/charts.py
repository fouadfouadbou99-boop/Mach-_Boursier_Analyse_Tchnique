import plotly.graph_objects as go


def plot_main_chart(
    df,
    supports,
    resistances
):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            name="MASI",
            line=dict(width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA20"],
            name="SMA20"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA50"],
            name="SMA50"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["SMA200"],
            name="SMA200"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["BB_UPPER"],
            name="BB Upper",
            line=dict(dash="dot")
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["BB_LOWER"],
            name="BB Lower",
            line=dict(dash="dot")
        )
    )

    for s in supports:
        fig.add_hline(
            y=float(s),
            line_color="green"
        )

    for r in resistances:
        fig.add_hline(
            y=float(r),
            line_color="red"
        )

    return fig


def plot_rsi_chart(df):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["RSI"],
            name="RSI"
        )
    )

    fig.add_hline(y=70)
    fig.add_hline(y=30)

    return fig


def plot_macd_chart(df):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["MACD"],
            name="MACD"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["MACD_SIGNAL"],
            name="Signal"
        )
    )

    fig.add_bar(
        x=df["Date"],
        y=df["MACD_HIST"],
        name="Histogramme"
    )

    return fig


def plot_equity_curve(bt):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=bt["equity"],
            mode="lines",
            name="Equity Curve"
        )
    )

    return fig
