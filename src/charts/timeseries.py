from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

DEFAULT_CHART_START = pd.Timestamp("1960-01-01")


def _from_default_start(series: pd.Series | None) -> pd.Series | None:
    if series is None or series.empty:
        return series
    return series[series.index >= DEFAULT_CHART_START]


def add_recession_shading(fig: go.Figure, recession: pd.Series | None):
    recession = _from_default_start(recession)
    if recession is None or recession.empty:
        return fig
    active = recession.fillna(0).astype(int)
    starts=[]; start=None
    for dt, val in active.items():
        if val == 1 and start is None: start=dt
        if val == 0 and start is not None:
            starts.append((start, dt)); start=None
    if start is not None: starts.append((start, active.index[-1]))
    for a,b in starts:
        fig.add_vrect(x0=a, x1=b, opacity=0.12, line_width=0)
    return fig


def line_chart(series: pd.Series, title: str, recession: pd.Series | None = None, zero_line: bool=False, start_at_data: bool=False, robust_y: bool=False):
    series = series.dropna().sort_index()
    if not start_at_data:
        series = _from_default_start(series)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=series.index,y=series.values,mode="lines",name=title))
    if zero_line: fig.add_hline(y=0,line_dash="dash",opacity=0.5)
    add_recession_shading(fig,recession)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        template="plotly_dark",
        height=430,
        margin=dict(l=18,r=18,t=52,b=18),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Helvetica Neue, Arial", color="#ECEBF3"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(199,214,213,0.16)", tickfont=dict(color="#C7D6D5"))
    fig.update_yaxes(gridcolor="rgba(199,214,213,0.08)", zerolinecolor="rgba(199,214,213,0.16)", tickfont=dict(color="#C7D6D5"))
    if not series.empty:
        xmin = series.index.min() if start_at_data else DEFAULT_CHART_START
        fig.update_xaxes(range=[xmin, series.index.max()])
        if robust_y and len(series) >= 8:
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                if zero_line:
                    lower = min(lower, 0.0)
                    upper = max(upper, 0.0)
                pad = max((upper - lower) * 0.08, 1e-9)
                y0, y1 = lower - pad, upper + pad
                clipped = ((series < y0) | (series > y1)).any()
                fig.update_yaxes(range=[y0, y1])
                if clipped:
                    fig.add_annotation(
                        x=1, y=1, xref="paper", yref="paper",
                        text="Robust scale — extreme observations outside visible range",
                        showarrow=False, xanchor="right", yanchor="bottom",
                        font=dict(size=11), opacity=0.65,
                    )
    return fig
