from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

def add_recession_shading(fig: go.Figure, recession: pd.Series | None):
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

def line_chart(series: pd.Series, title: str, recession: pd.Series | None = None, zero_line: bool=False):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=series.index,y=series.values,mode="lines",name=title))
    if zero_line: fig.add_hline(y=0,line_dash="dash",opacity=0.5)
    add_recession_shading(fig,recession)
    fig.update_layout(title=title, template="plotly_dark", height=430, margin=dict(l=20,r=20,t=55,b=20), showlegend=False)
    return fig
