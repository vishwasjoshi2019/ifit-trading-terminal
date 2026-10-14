import numpy as np
import pandas as pd
import plotly.graph_objects as go


def build_cluster_footprint_figure(
    footprint_df,
    title="Developing Order Flow Footprint",
):
    df = footprint_df.copy()
    if df.empty:
        return go.Figure()

    df = df.sort_values("Price")
    prices = df["Price"].to_numpy()
    bid = df["Bid Volume"].to_numpy()
    ask = df["Ask Volume"].to_numpy()
    delta = df["Delta"].to_numpy()
    total = df["Total Volume"].to_numpy()

    if len(prices) > 1:
        step = float(np.median(np.diff(prices)))
        step = abs(step) if step else 1.0
    else:
        step = 1.0

    fig = go.Figure()

    # Bid volume bars extend left.
    fig.add_trace(
        go.Bar(
            x=-bid,
            y=prices,
            orientation="h",
            name="Bid",
            customdata=np.column_stack([ask, total, delta]),
            hovertemplate=(
                "Price: %{y:,.2f}<br>"
                "Bid: %{x:,.0f}<br>"
                "Ask: %{customdata[0]:,.0f}<br>"
                "Total: %{customdata[1]:,.0f}<br>"
                "Delta: %{customdata[2]:+,.0f}"
                "<extra></extra>"
            ),
        )
    )

    # Ask volume bars extend right.
    fig.add_trace(
        go.Bar(
            x=ask,
            y=prices,
            orientation="h",
            name="Ask",
            customdata=np.column_stack([bid, total, delta]),
            hovertemplate=(
                "Price: %{y:,.2f}<br>"
                "Ask: %{x:,.0f}<br>"
                "Bid: %{customdata[0]:,.0f}<br>"
                "Total: %{customdata[1]:,.0f}<br>"
                "Delta: %{customdata[2]:+,.0f}"
                "<extra></extra>"
            ),
        )
    )

    # POC line.
    poc = float(df["POC"].iloc[-1])
    fig.add_hline(
        y=poc,
        line_dash="dash",
        annotation_text=f"POC {poc:,.2f}",
        annotation_position="top right",
    )

    # Zero axis separating bid and ask.
    fig.add_vline(x=0, line_width=1)

    fig.update_layout(
        title=title,
        barmode="relative",
        height=650,
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis_title="Bid Volume  ←  |  →  Ask Volume",
        yaxis_title="Price",
        legend=dict(orientation="h"),
        hovermode="closest",
    )

    fig.update_yaxes(
        dtick=step if step <= 100 else None,
        showgrid=True,
    )

    return fig


def build_delta_intensity_figure(footprint_df, title="Delta Intensity"):
    df = footprint_df.copy().sort_values("Price")
    if df.empty:
        return go.Figure()

    fig = go.Figure(
        go.Bar(
            x=df["Delta"],
            y=df["Price"],
            orientation="h",
            customdata=np.column_stack(
                [
                    df["Bid Volume"],
                    df["Ask Volume"],
                    df["Total Volume"],
                    df["Bid/Ask Imbalance"],
                ]
            ),
            hovertemplate=(
                "Price: %{y:,.2f}<br>"
                "Delta: %{x:+,.0f}<br>"
                "Bid: %{customdata[0]:,.0f}<br>"
                "Ask: %{customdata[1]:,.0f}<br>"
                "Total: %{customdata[2]:,.0f}<br>"
                "Imbalance: %{customdata[3]:.2f}x"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(x=0, line_width=1)
    fig.update_layout(
        title=title,
        height=500,
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis_title="Delta",
        yaxis_title="Price",
        showlegend=False,
    )
    return fig


def footprint_event_counts(footprint_df):
    df = footprint_df
    return {
        "Absorption": int(df["Absorption"].sum()),
        "Exhaustion": int(df["Exhaustion"].sum()),
        "Stacked Imbalance": int(df["Stacked Imbalance"].sum()),
        "Delta Flip": int(df["Delta Flip"].sum()),
        "Failed Auction": int(df["Failed Auction"].sum()),
        "Large Print": int(df["Large Print"].sum()),
    }
