"""IFIT V0.8.4 — Advanced Interactive Chart Engine.

Provider-neutral chart analytics. Uses OHLCV data supplied by IFIT and builds
TradingView-style interactive Plotly charts with configurable indicators,
sub-panels and drawing tools. No order placement logic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=int(n), adjust=False).mean()


def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(int(n), min_periods=1).mean()


def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100/(1+rs)).fillna(50)


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = _ema(close, fast) - _ema(close, slow)
    sig = _ema(line, signal)
    return line, sig, line - sig


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["Close"].shift(1)
    tr = pd.concat([(df["High"]-df["Low"]), (df["High"]-prev).abs(), (df["Low"]-prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()


def _bollinger(close: pd.Series, n: int = 20, mult: float = 2.0):
    mid = _sma(close, n)
    std = close.rolling(n, min_periods=1).std().fillna(0)
    return mid, mid + mult*std, mid - mult*std


def _supertrend(df: pd.DataFrame, n: int = 10, mult: float = 3.0):
    atr = _atr(df, n)
    hl2 = (df["High"] + df["Low"]) / 2
    upper = hl2 + mult * atr
    lower = hl2 - mult * atr
    trend = pd.Series(1, index=df.index, dtype=float)
    st = pd.Series(index=df.index, dtype=float)
    for i in range(len(df)):
        if i == 0:
            st.iloc[i] = upper.iloc[i]
            continue
        if df["Close"].iloc[i] > upper.iloc[i-1]:
            trend.iloc[i] = 1
        elif df["Close"].iloc[i] < lower.iloc[i-1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i-1]
            if trend.iloc[i] > 0:
                lower.iloc[i] = max(lower.iloc[i], lower.iloc[i-1])
            else:
                upper.iloc[i] = min(upper.iloc[i], upper.iloc[i-1])
        st.iloc[i] = lower.iloc[i] if trend.iloc[i] > 0 else upper.iloc[i]
    return st, trend


def calculate_indicators(df: pd.DataFrame, selections: list[str], params: dict) -> dict:
    close = df["Close"]
    out = {}
    if "EMA" in selections:
        out["EMA"] = _ema(close, params.get("ema", 20))
    if "SMA" in selections:
        out["SMA"] = _sma(close, params.get("sma", 50))
    if "VWAP" in selections and "VWAP" in df:
        out["VWAP"] = df["VWAP"]
    if "Bollinger Bands" in selections:
        out["BB Mid"], out["BB Upper"], out["BB Lower"] = _bollinger(close, params.get("bb", 20), params.get("bb_mult", 2.0))
    if "Supertrend" in selections:
        out["Supertrend"], out["Supertrend Direction"] = _supertrend(df, params.get("st_period", 10), params.get("st_mult", 3.0))
    if "RSI" in selections:
        out["RSI"] = _rsi(close, params.get("rsi", 14))
    if "MACD" in selections:
        out["MACD"], out["MACD Signal"], out["MACD Hist"] = _macd(close, params.get("macd_fast", 12), params.get("macd_slow", 26), params.get("macd_signal", 9))
    if "ATR" in selections:
        out["ATR"] = _atr(df, params.get("atr", 14))
    if "Volume" in selections:
        out["Volume"] = df["Volume"]
    if "CVD" in selections:
        out["CVD"] = df["CVD"]
    if "Delta" in selections:
        out["Delta"] = df["Delta"]
    return out



def add_native_footprint_overlay(
    fig,
    df: pd.DataFrame,
    footprint_df: pd.DataFrame | None = None,
    max_bars: int = 20,
    levels_per_bar: int = 5,
    compact: bool = False,
):
    """
    CHT Native Footprint V0.3.

    Professional candle-integrated footprint layer.

    Reuses the existing frozen IFIT footprint engine and exposes
    its existing flow/intelligence fields directly on the CHT
    price pane.

    Simulation/proxy data until an authorized tick/depth feed
    is connected.
    """

    if fig is None or df is None or df.empty:
        return fig

    if footprint_df is None or footprint_df.empty:
        return fig

    required = {
        "Bar",
        "Price",
        "Bid Volume",
        "Ask Volume",
    }

    if not required.issubset(
        set(footprint_df.columns)
    ):
        return fig

    chart = df.tail(
        min(int(max_bars), len(df))
    ).copy()

    if chart.empty:
        return fig

    source_bars = sorted(
        footprint_df["Bar"].dropna().unique()
    )

    if not source_bars:
        return fig

    source_bars = source_bars[-len(chart):]

    chart_bars = chart["Bar"].tolist()[
        -len(source_bars):
    ]

    if not chart_bars:
        return fig

    # --------------------------------------------------------
    # X GEOMETRY
    # --------------------------------------------------------
    if len(chart_bars) > 1:
        diffs = np.diff(
            np.asarray(
                chart_bars,
                dtype=float,
            )
        )

        x_step = float(
            np.median(diffs)
        ) if len(diffs) else 1.0
    else:
        x_step = 1.0

    cluster_width = max(
        0.34,
        min(
            0.54,
            x_step * 0.54,
        ),
    )

    half_width = cluster_width / 2.0

    annotations = list(
        getattr(
            fig.layout,
            "annotations",
            [],
        )
        or []
    )

    shapes = list(
        getattr(
            fig.layout,
            "shapes",
            [],
        )
        or []
    )

    # --------------------------------------------------------
    # HELPER: BOOLEAN EVENT VALUE
    # --------------------------------------------------------
    def _event(row, name):
        if name not in row.index:
            return False

        value = row[name]

        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float, np.integer, np.floating)):
            return bool(value)

        text = str(value).strip().upper()

        return text not in {
            "",
            "0",
            "0.0",
            "FALSE",
            "NO",
            "NONE",
            "NAN",
            "NEUTRAL",
        }

    # --------------------------------------------------------
    # EVENT PRIORITY / DISPLAY
    # --------------------------------------------------------
    event_specs = [
        ("Failed Auction", "FA", "#ff9f43"),
        ("Absorption", "ABS", "#ffd746"),
        ("Exhaustion", "EXH", "#ff7070"),
        ("Delta Flip", "DF", "#b78cff"),
        ("Stacked Imbalance", "SI", "#55d98b"),
        ("Large Print", "LP", "#58c7ff"),
        ("HVN", "HVN", "#f3c969"),
        ("LVN", "LVN", "#9aa8ff"),
    ]

    # --------------------------------------------------------
    # CANDLE-LEVEL PROCESSING
    # --------------------------------------------------------
    for target_bar, source_bar in zip(
        chart_bars,
        source_bars,
    ):

        candle_rows = chart[
            chart["Bar"] == target_bar
        ]

        if candle_rows.empty:
            continue

        candle = candle_rows.iloc[0]

        low = float(candle["Low"])
        high = float(candle["High"])
        open_ = float(candle["Open"])
        close = float(candle["Close"])

        if not (
            np.isfinite(low)
            and np.isfinite(high)
            and high > low
        ):
            continue

        source = footprint_df[
            footprint_df["Bar"] == source_bar
        ].copy()

        if source.empty:
            continue

        source["Price"] = pd.to_numeric(
            source["Price"],
            errors="coerce",
        )

        source["Bid Volume"] = pd.to_numeric(
            source["Bid Volume"],
            errors="coerce",
        ).fillna(0.0)

        source["Ask Volume"] = pd.to_numeric(
            source["Ask Volume"],
            errors="coerce",
        ).fillna(0.0)

        source = source.dropna(
            subset=["Price"]
        )

        if source.empty:
            continue

        source = source.sort_values(
            "Price"
        ).reset_index(drop=True)

        # ----------------------------------------------------
        # SELECT LEVELS
        # ----------------------------------------------------
        level_count = min(
            int(levels_per_bar),
            len(source),
        )

        if len(source) > level_count:

            positions = np.linspace(
                0,
                len(source) - 1,
                level_count,
            ).round().astype(int)

            positions = np.unique(
                positions
            )

            source = source.iloc[
                positions
            ].copy()

        source = source.reset_index(
            drop=True
        )

        if source.empty:
            continue

        # ----------------------------------------------------
        # CANDLE-CENTERED FOOTPRINT RANGE
        # ----------------------------------------------------
        candle_range = max(
            high - low,
            1e-9,
        )

        body_high = max(
            open_,
            close,
        )

        body_low = min(
            open_,
            close,
        )

        body_mid = (
            body_high + body_low
        ) / 2.0

        footprint_half_range = max(
            candle_range * 0.34,
            candle_range * 0.18,
        )

        mapped_low = max(
            low,
            body_mid - footprint_half_range,
        )

        mapped_high = min(
            high,
            body_mid + footprint_half_range,
        )

        if mapped_high <= mapped_low:
            mapped_low = low
            mapped_high = high

        src_low = float(
            source["Price"].min()
        )

        src_high = float(
            source["Price"].max()
        )

        if (
            np.isfinite(src_low)
            and np.isfinite(src_high)
            and src_high > src_low
            and len(source) > 1
        ):
            source["Mapped Price"] = (
                mapped_low
                + (
                    (
                        source["Price"]
                        - src_low
                    )
                    / (
                        src_high
                        - src_low
                    )
                )
                * (
                    mapped_high
                    - mapped_low
                )
            )
        else:
            source["Mapped Price"] = np.linspace(
                mapped_low,
                mapped_high,
                len(source),
            )

        level_height = (
            (
                mapped_high
                - mapped_low
            )
            / max(
                len(source),
                2,
            )
        ) * 0.80

        level_height = max(
            level_height,
            candle_range * 0.045,
        )

        # ----------------------------------------------------
        # TOTAL / POC / DELTA
        # ----------------------------------------------------
        source["Total"] = (
            source["Bid Volume"].abs()
            + source["Ask Volume"].abs()
        )

        max_total = float(
            source["Total"].max()
        )

        if not np.isfinite(max_total):
            max_total = 1.0

        max_total = max(
            max_total,
            1.0,
        )

        poc_idx = int(
            source["Total"].idxmax()
        )

        candle_delta = float(
            source["Ask Volume"].sum()
            - source["Bid Volume"].sum()
        )

        # ----------------------------------------------------
        # FOOTPRINT CELLS
        # ----------------------------------------------------
        for idx, row in source.iterrows():

            y = float(
                row["Mapped Price"]
            )

            bid = max(
                float(row["Bid Volume"]),
                0.0,
            )

            ask = max(
                float(row["Ask Volume"]),
                0.0,
            )

            total = max(
                bid + ask,
                1.0,
            )

            intensity = min(
                1.0,
                total / max_total,
            )

            bid_share = bid / total
            ask_share = ask / total

            imbalance_ratio = max(
                bid / max(ask, 1.0),
                ask / max(bid, 1.0),
            )

            is_poc = (
                idx == poc_idx
            )

            strong_imbalance = (
                imbalance_ratio >= 2.0
            )

            if is_poc:
                border_color = (
                    "rgba(255,215,70,0.98)"
                )
                border_width = 1.5

            elif strong_imbalance:
                border_color = (
                    "rgba(255,255,255,0.92)"
                )
                border_width = 1.0

            else:
                border_color = (
                    "rgba(150,160,175,0.28)"
                )
                border_width = 0.35

            bid_alpha = min(
                0.68,
                0.18
                + 0.48
                * max(
                    bid_share,
                    0.18,
                )
                * intensity,
            )

            ask_alpha = min(
                0.68,
                0.18
                + 0.48
                * max(
                    ask_share,
                    0.18,
                )
                * intensity,
            )

            # BID
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=(
                        float(target_bar)
                        - half_width
                    ),
                    x1=float(target_bar),
                    y0=(
                        y
                        - level_height / 2
                    ),
                    y1=(
                        y
                        + level_height / 2
                    ),
                    line=dict(
                        width=border_width,
                        color=border_color,
                    ),
                    fillcolor=(
                        "rgba(55,145,235,"
                        f"{bid_alpha:.3f})"
                    ),
                    layer="above",
                )
            )

            # ASK
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=float(target_bar),
                    x1=(
                        float(target_bar)
                        + half_width
                    ),
                    y0=(
                        y
                        - level_height / 2
                    ),
                    y1=(
                        y
                        + level_height / 2
                    ),
                    line=dict(
                        width=border_width,
                        color=border_color,
                    ),
                    fillcolor=(
                        "rgba(235,80,85,"
                        f"{ask_alpha:.3f})"
                    ),
                    layer="above",
                )
            )

            # Bid | Ask
            annotations.append(
                dict(
                    x=float(target_bar),
                    y=y,
                    xref="x",
                    yref="y",
                    text=(
                        f"{bid/1000:.1f}"
                        "│"
                        f"{ask/1000:.1f}"
                    ),
                    showarrow=False,
                    font=dict(
                        size=6,
                        color="#ffffff",
                    ),
                    align="center",
                    bgcolor=(
                        "rgba(5,8,12,0.52)"
                    ),
                    borderpad=0,
                )
            )

        # ----------------------------------------------------
        # POC
        # ----------------------------------------------------
        poc_row = source.loc[poc_idx]

        poc_y = float(
            poc_row["Mapped Price"]
        )

        annotations.append(
            dict(
                x=(
                    float(target_bar)
                    + half_width
                    + x_step * 0.05
                ),
                y=poc_y,
                xref="x",
                yref="y",
                text="POC",
                showarrow=False,
                font=dict(
                    size=5,
                    color="#ffd746",
                ),
                bgcolor=(
                    "rgba(0,0,0,0.40)"
                ),
                borderpad=0,
            )
        )

        # ----------------------------------------------------
        # CANDLE DELTA
        # ----------------------------------------------------
        delta_color = (
            "#55d98b"
            if candle_delta > 0
            else "#ff7070"
            if candle_delta < 0
            else "#cccccc"
        )

        delta_y = (
            high + candle_range * 0.055
            if candle_delta >= 0
            else
            low - candle_range * 0.055
        )

        annotations.append(
            dict(
                x=float(target_bar),
                y=delta_y,
                xref="x",
                yref="y",
                text=(
                    f"Δ {candle_delta:+,.0f}"
                ),
                showarrow=False,
                font=dict(
                    size=5,
                    color=delta_color,
                ),
                bgcolor=(
                    "rgba(0,0,0,0.28)"
                ),
                borderpad=1,
            )
        )

        # ----------------------------------------------------
        # FLOW EVENT MARKERS
        # ----------------------------------------------------
        active_events = []

        for column, short_name, marker_color in event_specs:
            if column in source.columns:
                event_rows = source[
                    source[column].apply(
                        lambda x: (
                            False
                            if pd.isna(x)
                            else (
                                bool(x)
                                if isinstance(
                                    x,
                                    (bool, np.bool_),
                                )
                                else str(x).strip().upper()
                                not in {
                                    "",
                                    "0",
                                    "0.0",
                                    "FALSE",
                                    "NO",
                                    "NONE",
                                    "NAN",
                                    "NEUTRAL",
                                }
                            )
                        )
                    )
                ]

                if not event_rows.empty:
                    active_events.append(
                        (
                            short_name,
                            marker_color,
                        )
                    )

        # Render at most 4 compact event tags per candle.
        active_events = active_events[:4]

        for event_index, (
            short_name,
            marker_color,
        ) in enumerate(active_events):

            annotations.append(
                dict(
                    x=(
                        float(target_bar)
                        - half_width
                        - x_step * 0.06
                    ),
                    y=(
                        high
                        - candle_range
                        * (
                            0.08
                            + event_index * 0.065
                        )
                    ),
                    xref="x",
                    yref="y",
                    text=short_name,
                    showarrow=False,
                    font=dict(
                        size=4,
                        color=marker_color,
                    ),
                    bgcolor=(
                        "rgba(0,0,0,0.42)"
                    ),
                    borderpad=1,
                )
            )

    # --------------------------------------------------------
    # APPLY
    # --------------------------------------------------------
    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
    )

    return fig

def build_interactive_figure(df: pd.DataFrame, chart_type: str, selections: list[str], params: dict,
                             show_poc: bool = True, poc: float | None = None,
                             show_volume_profile: bool = False, profile: pd.DataFrame | None = None,
                             show_cvd: bool = False, show_delta: bool = False,
                             show_native_footprint: bool = False,
                             footprint_df: pd.DataFrame | None = None):
    inds = calculate_indicators(df, selections, params)
    lower = []
    if "RSI" in selections: lower.append("RSI")
    if "MACD" in selections: lower.append("MACD")
    if "ATR" in selections: lower.append("ATR")
    if "Volume" in selections or show_delta: lower.append("FLOW")
    if "CVD" in selections or show_cvd: lower.append("CVD")
    lower = list(dict.fromkeys(lower))
    rows = 1 + len(lower)
    heights = [0.62] + [0.38/len(lower)] * len(lower) if lower else [1.0]
    titles = ["Price"] + lower
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.025,
                        row_heights=heights, subplot_titles=titles)
    x = df["Bar"]
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(x=x, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"), row=1, col=1)
    elif chart_type == "Line":
        fig.add_trace(go.Scatter(x=x, y=df["Close"], mode="lines", name="Close"), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(x=x, y=df["Close"], mode="lines", fill="tozeroy", name="Close"), row=1, col=1)

    overlay_names = {"EMA","SMA","VWAP","BB Mid","BB Upper","BB Lower","Supertrend"}
    for name in overlay_names.intersection(inds):
        fig.add_trace(go.Scatter(x=x, y=inds[name], mode="lines", name=name), row=1, col=1)

    if show_poc and poc is not None and np.isfinite(poc):
        fig.add_hline(y=float(poc), line_dash="dot", annotation_text="POC", row=1, col=1)

    if show_volume_profile and profile is not None and not profile.empty:
        # Render Volume Profile in the primary price coordinate system.
        # Normalize volume into chart-bar width so it cannot distort the X-axis.
        _vp_max = float(profile["Volume"].max()) if not profile.empty else 0.0
        _chart_right = float(df["Bar"].max()) if not df.empty else 0.0

        if _vp_max > 0 and np.isfinite(_vp_max) and np.isfinite(_chart_right):
            _vp_width = (
                profile["Volume"].astype(float) / _vp_max
            ) * max(5.0, len(df) * 0.20)

            _vp_base = _chart_right - _vp_width

            fig.add_trace(
                go.Bar(
                    x=_vp_width,
                    base=_vp_base,
                    y=profile["Price"],
                    orientation="h",
                    name="Volume Profile",
                    opacity=0.35,
                    hovertemplate="Price %{y:.2f}<br>Volume %{customdata:,.0f}<extra></extra>",
                    customdata=profile["Volume"],
                ),
                row=1,
                col=1,
            )

    r = 2
    for pane in lower:
        if pane == "RSI" and "RSI" in inds:
            fig.add_trace(go.Scatter(x=x, y=inds["RSI"], mode="lines", name="RSI"), row=r, col=1)
            fig.add_hline(y=70, line_dash="dot", row=r, col=1)
            fig.add_hline(y=30, line_dash="dot", row=r, col=1)
        elif pane == "MACD" and "MACD" in inds:
            fig.add_trace(go.Bar(x=x, y=inds["MACD Hist"], name="MACD Hist"), row=r, col=1)
            fig.add_trace(go.Scatter(x=x, y=inds["MACD"], mode="lines", name="MACD"), row=r, col=1)
            fig.add_trace(go.Scatter(x=x, y=inds["MACD Signal"], mode="lines", name="Signal"), row=r, col=1)
        elif pane == "ATR" and "ATR" in inds:
            fig.add_trace(go.Scatter(x=x, y=inds["ATR"], mode="lines", name="ATR"), row=r, col=1)
        elif pane == "FLOW":
            if "Volume" in inds:
                fig.add_trace(go.Bar(x=x, y=inds["Volume"], name="Volume"), row=r, col=1)
            if show_delta or "Delta" in inds:
                fig.add_trace(go.Bar(x=x, y=inds.get("Delta", df["Delta"]), name="Delta"), row=r, col=1)
        elif pane == "CVD":
            fig.add_trace(go.Scatter(x=x, y=inds.get("CVD", df["CVD"]), mode="lines", name="CVD"), row=r, col=1)
        r += 1

    fig.update_layout(
        height=max(620, 440 + 150*len(lower)),
        margin=dict(l=45, r=25, t=55, b=35),
        hovermode="x unified",
        dragmode="pan",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
        xaxis_rangeslider_visible=False,
        uirevision="ifit-chart-v084",
    )
    if show_volume_profile and profile is not None and not profile.empty:
        fig.update_layout(xaxis2=dict(overlaying="x", side="top", showgrid=False, showticklabels=False, title=None, zeroline=False))
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor", showline=True)
    fig.update_yaxes(showspikes=True, spikemode="across", showline=True, side="right", row=1, col=1)

    if show_native_footprint and footprint_df is not None:
        fig = add_native_footprint_overlay(
            fig,
            df,
            footprint_df=footprint_df,
            max_bars=min(20, len(df)),
            levels_per_bar=5,
            compact=len(df) > 120,
        )

        # ----------------------------------------------------
        # CHT Native Footprint V0.2.3 FOCUS MODE
        #
        # Preserve the full OHLCV dataset and indicators,
        # but focus the visible chart on the recent order-flow
        # region so the candle-integrated footprint is readable.
        # ----------------------------------------------------
        try:
            focus_bars = min(
                40,
                len(df),
            )

            last_bar = float(
                df["Bar"].iloc[-1]
            )

            first_focus_bar = float(
                df["Bar"].iloc[-focus_bars]
            )

            fig.update_xaxes(
                range=[
                    first_focus_bar - 0.5,
                    last_bar + 0.8,
                ],
                autorange=False,
            )

        except Exception:
            # Focus mode must never break the CHT chart.
            pass

    return fig


def chart_capabilities() -> list[dict]:
    return [
        {"Capability":"Interactive candles","Status":"READY","Notes":"Zoom, pan, hover and range selection"},
        {"Capability":"Indicator stack","Status":"READY","Notes":"Multiple overlays and lower panes"},
        {"Capability":"Drawing tools","Status":"READY","Notes":"Line, rectangle, circle, open path and erase"},
        {"Capability":"Volume Profile","Status":"READY","Notes":"IFIT profile data can be displayed"},
        {"Capability":"IFIT flow overlays","Status":"READY","Notes":"CVD and Delta remain provider-labelled"},
        {"Capability":"Saved layouts","Status":"V0.8.4 FOUNDATION","Notes":"Template persistence is next engine layer"},
    ]
