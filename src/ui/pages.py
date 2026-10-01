from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app_core import MacroMonitor
from src.charts.timeseries import DEFAULT_CHART_START, line_chart
from src.ui.helpers import fmt, signal_label

@st.cache_resource
def get_monitor(project_root: str):
    return MacroMonitor(project_root)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_metrics(project_root: str, indicator_id: str):
    return get_monitor(project_root).metrics(indicator_id)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_composite(project_root: str, category: str):
    return get_monitor(project_root).category_composite(category)


def setup_page(title: str):
    st.set_page_config(page_title=title, page_icon="📈", layout="wide")
    st.markdown("""
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1900px;}
    [data-testid="stMetric"] {background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.08); padding: .8rem; border-radius: .55rem;}
    .small-muted {opacity: .68; font-size: .88rem;}
    </style>
    """, unsafe_allow_html=True)


def _recession(project_root: str) -> pd.Series:
    mon = get_monitor(project_root)
    try:
        df = mon.repo.load("__USREC")
        if df.empty:
            from src.data_sources.fred import FredCSVSource
            df = FredCSVSource().fetch({"series_id": "USREC"})
            mon.repo.upsert_observations("__USREC", df, "fred")
        return df.set_index("observation_date")["value"].resample("ME").last()
    except Exception:
        return pd.Series(dtype=float)


def _latest(df: pd.DataFrame, col: str):
    if df.empty or col not in df or not df[col].notna().any():
        return np.nan
    return df[col].dropna().iloc[-1]


def _category_table(project_root: str, category: str) -> pd.DataFrame:
    mon = get_monitor(project_root)
    rows=[]
    for spec in mon.registry.by_category(category):
        m=cached_metrics(project_root,spec["id"])
        if m.empty:
            rows.append({"Indicator": spec["short_name"], "Signal": np.nan, "Level": np.nan, "YoY %": np.nan, "Momentum": np.nan, "Data": "Missing", "ID": spec["id"]})
            continue
        rows.append({
            "Indicator": spec["short_name"],
            "Signal": _latest(m,"signal"),
            "Level": _latest(m,"level"),
            "YoY %": _latest(m,"yoy_pct"),
            "Momentum": _latest(m,"momentum"),
            "Data": "Exact" if spec.get("exact") else "Proxy",
            "ID": spec["id"],
        })
    return pd.DataFrame(rows)


def _heatmap(project_root: str, category: str):
    table=_category_table(project_root,category)
    metrics=["Signal","Momentum"]
    z=table[metrics].astype(float).to_numpy()
    text=np.vectorize(lambda x: "—" if pd.isna(x) else f"{x:.2f}")(z)
    fig=go.Figure(data=go.Heatmap(
        z=z, x=metrics, y=table["Indicator"], text=text, texttemplate="%{text}",
        zmid=0, zmin=-2, zmax=2, colorscale="RdYlGn", colorbar=dict(title="σ")
    ))
    fig.update_layout(template="plotly_dark", height=max(360, 46*len(table)), margin=dict(l=15,r=20,t=30,b=25))
    return fig


def _composite_metrics(project_root: str, category: str):
    comp=cached_composite(project_root,category)
    return comp, _latest(comp,"score"), _latest(comp,"positive_breadth"), int(_latest(comp,"coverage")) if not pd.isna(_latest(comp,"coverage")) else 0


def render_overview(project_root: str):
    setup_page("U.S. Business Cycle Monitor")
    st.title("U.S. Business Cycle Monitor")
    st.caption("A personal macro research terminal: leading, coincident and lagging business-cycle evidence.")
    mon=get_monitor(project_root)
    if st.button("Refresh all data", type="primary"):
        with st.spinner("Refreshing public and configured manual sources..."):
            mon.refresh_all()
            st.cache_data.clear()
        st.success("Refresh complete. Missing licensed/manual inputs remain excluded rather than fabricated.")

    lead, ls, lb, lc = _composite_metrics(project_root,"leading")
    coi, cs, cb, cc = _composite_metrics(project_root,"coincident")
    cchange = coi["score"].diff(3).dropna().iloc[-1] if not coi.empty and coi["score"].diff(3).notna().any() else np.nan
    from src.analytics.composites import classify_regime
    regime,growth,momentum=classify_regime(cs,ls,cchange)

    a,b,c,d=st.columns(4)
    a.metric("Macro regime", regime)
    b.metric("Growth", f"{fmt(growth)}σ")
    c.metric("Momentum", f"{fmt(momentum)}σ")
    d.metric("Latest common signal", max(lead.index.max() if not lead.empty else pd.Timestamp.min, coi.index.max() if not coi.empty else pd.Timestamp.min).strftime("%b %Y") if (not lead.empty or not coi.empty) else "N/A")

    a,b=st.columns(2)
    with a:
        st.subheader("Leading")
        x,y,z=st.columns(3)
        x.metric("Composite", f"{fmt(ls)}σ", signal_label(ls))
        y.metric("Positive breadth", f"{lb*100:.0f}%" if not pd.isna(lb) else "N/A")
        z.metric("Coverage", f"{lc}/10")
        st.plotly_chart(_heatmap(project_root,"leading"), use_container_width=True)
    with b:
        st.subheader("Coincident")
        x,y,z=st.columns(3)
        x.metric("Composite", f"{fmt(cs)}σ", signal_label(cs))
        y.metric("Positive breadth", f"{cb*100:.0f}%" if not pd.isna(cb) else "N/A")
        z.metric("Coverage", f"{cc}/4")
        st.plotly_chart(_heatmap(project_root,"coincident"), use_container_width=True)

    st.subheader("Composite history")
    recession=_recession(project_root)
    fig=go.Figure()
    if not lead.empty: fig.add_trace(go.Scatter(x=lead.index,y=lead["score"],name="Leading",mode="lines"))
    if not coi.empty: fig.add_trace(go.Scatter(x=coi.index,y=coi["score"],name="Coincident",mode="lines"))
    if not recession.empty:
        active=recession[recession.index >= DEFAULT_CHART_START].fillna(0).astype(int); start=None
        for dt,val in active.items():
            if val==1 and start is None: start=dt
            elif val==0 and start is not None:
                fig.add_vrect(x0=start,x1=dt,opacity=.11,line_width=0); start=None
    fig.add_hline(y=0,line_dash="dash",opacity=.5)
    fig.update_layout(template="plotly_dark",height=450,margin=dict(l=20,r=20,t=20,b=20),legend=dict(orientation="h"))
    xmax_candidates=[]\n    if not lead.empty: xmax_candidates.append(lead.index.max())\n    if not coi.empty: xmax_candidates.append(coi.index.max())\n    if xmax_candidates:\n        fig.update_xaxes(range=[DEFAULT_CHART_START, max(xmax_candidates)])
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("Lagging conditions")
    lag=_category_table(project_root,"lagging")
    st.dataframe(lag[["Indicator","Level","YoY %","Momentum","Data"]], use_container_width=True, hide_index=True)


def render_category(project_root: str, category: str):
    title={"leading":"Leading Indicators","coincident":"Coincident Indicators","lagging":"Lagging Indicators"}[category]
    setup_page(title)
    st.title(title)
    if category != "lagging":
        comp, score, breadth, coverage=_composite_metrics(project_root,category)
        c1,c2,c3=st.columns(3)
        c1.metric("Composite", f"{fmt(score)}σ", signal_label(score))
        c2.metric("Positive breadth", f"{breadth*100:.0f}%" if not pd.isna(breadth) else "N/A")
        target=10 if category=="leading" else 4
        c3.metric("Coverage",f"{coverage}/{target}")
        recession=_recession(project_root)
        st.plotly_chart(line_chart(comp["score"].dropna(), f"{title} composite", recession, zero_line=True),use_container_width=True)
        st.subheader("Current signal heatmap")
        st.plotly_chart(_heatmap(project_root,category),use_container_width=True)
    table=_category_table(project_root,category)
    st.subheader("Indicator monitor")
    st.dataframe(table[["Indicator","Signal","YoY %","Momentum","Data"]],use_container_width=True,hide_index=True)
    if category=="lagging":
        st.caption("Lagging indicators are diagnostics, not forced into a single good/bad composite. Contextual series may have a statistical z-score while retaining neutral economic directionality.")


def render_indicator(project_root: str):
    setup_page("Indicator Research")
    mon=get_monitor(project_root)
    specs=mon.registry.all()
    labels={s["name"]:s["id"] for s in specs}
    name=st.selectbox("Indicator",list(labels.keys()))
    spec=mon.registry.get(labels[name])
    m=cached_metrics(project_root,spec["id"])
    st.title(spec["name"])
    st.caption(spec.get("description",""))
    if spec.get("proxy_note"):
        st.warning(spec["proxy_note"])
    if m.empty:
        st.error("No data are currently available. If this is a manual/licensed indicator, populate its configured CSV and refresh.")
        return
    row=m.dropna(subset=["level"]).iloc[-1]
    a,b,c,d=st.columns(4)
    a.metric("Latest level",fmt(row.get("level")))
    b.metric("YoY",f"{fmt(row.get('yoy_pct'))}%")
    c.metric("Signal",f"{fmt(row.get('signal'))}σ",signal_label(row.get("signal")))
    d.metric("Momentum",f"{fmt(row.get('momentum'))}σ")
    metric=st.radio("View",["level","yoy_pct","growth_3m_ann","growth_6m_ann","signal","momentum"],horizontal=True)
    yrs=st.select_slider("History",options=[3,5,10,20,40],value=10)
    series=m[metric].dropna()
    cutoff=series.index.max()-pd.DateOffset(years=yrs) if not series.empty else None
    if cutoff is not None: series=series[series.index>=cutoff]
    st.plotly_chart(line_chart(series,metric.replace("_"," ").title(),_recession(project_root),zero_line=metric in {"yoy_pct","growth_3m_ann","growth_6m_ann","signal","momentum"}),use_container_width=True)
    st.markdown(f"**Source:** `{spec.get('provider')}`  ·  **Frequency:** {spec.get('frequency')}  ·  **Component quality:** {'Exact/public' if spec.get('exact') else 'Proxy/constructed'}")


def render_data_health(project_root: str):
    setup_page("Data & Releases")
    st.title("Data Health")
    mon=get_monitor(project_root)
    if st.button("Refresh all configured sources",type="primary"):
        with st.spinner("Refreshing..."):
            mon.refresh_all(); st.cache_data.clear()
        st.success("Refresh completed.")
    rows=[]
    now=pd.Timestamp.now().normalize()
    for spec in mon.registry.all():
        raw=mon.repo.load(spec["id"])
        latest=raw["observation_date"].max() if not raw.empty else pd.NaT
        age=(now-latest).days if pd.notna(latest) else None
        rows.append({"Indicator":spec["short_name"],"Category":spec["category"],"Provider":spec["provider"],"Latest observation":latest.date().isoformat() if pd.notna(latest) else "Missing","Age (days)":age,"Quality":"Exact" if spec.get("exact") else "Proxy","Status":"OK" if pd.notna(latest) else "Needs data"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.subheader("Update log")
    st.dataframe(mon.repo.recent_logs(),use_container_width=True,hide_index=True)
    st.info("For ISM New Orders, place a CSV with columns date,value at data/manual/ism_new_orders.csv, then refresh. This keeps proprietary/licensed data explicit rather than scraping an unofficial source.")
