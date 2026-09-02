import plotly.graph_objects as go

def plot_chart(df, supports, resistances):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            name="MASI"
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

    for s in supports:
        fig.add_hline(y=s, line_dash="dot")

    for r in resistances:
        fig.add_hline(y=r, line_dash="dash")

    return fig
