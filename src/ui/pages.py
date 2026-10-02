from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app_core import MacroMonitor
from src.charts.timeseries import DEFAULT_CHART_START, line_chart
from src.ui.helpers import fmt, signal_label

def get_monitor(project_root: str):
    return MacroMonitor(project_root)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_metrics(project_root: str, indicator_id: str):
    return get_monitor(project_root).metrics(indicator_id)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_composite(project_root: str, category: str):
    return get_monitor(project_root).category_composite(category)


def setup_page(title: str):
    st.set_page_config(page_title=title, page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
    st.markdown("""
    <style>
    :root {
        --onyx: #0C120C;
        --brick-ember: #C20114;
        --dim-grey: #6D7275;
        --ash-grey: #C7D6D5;
        --ghost-white: #ECEBF3;
    }
    html, body, .stApp, .stMarkdown, .stText, .stCaption, .stButton, .stSelectbox, .stRadio, .stSlider,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stDataFrame"] {
        font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: var(--onyx) !important;
        color: var(--ghost-white) !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: var(--ghost-white) !important;
    }
    h1, h2, h3, h4, h5, h6, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
        letter-spacing: -0.015em;
    }
    h1, h2, h3 {
        font-weight: 650 !important;
    }
    [data-testid="stMetricValue"] {
        font-weight: 600 !important;
    }
    .block-container {padding-top: 7.4rem; padding-bottom: 2rem; padding-left: 1.25rem !important; padding-right: 1.25rem !important; max-width: none !important; width: 100% !important;}
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    [data-testid="stMetric"] {
        background: rgba(109,114,117,0.18);
        border: 1px solid rgba(199,214,213,0.20);
        padding: .8rem;
        border-radius: .55rem;
    }
    .st-key-top_nav {
        position: fixed;
        top: 3.75rem;
        left: 1rem;
        right: 1rem;
        width: auto;
        box-sizing: border-box;
        max-width: calc(100vw - 2rem);
        z-index: 9999;
        background: rgba(12,18,12,0.98);
        border: 1px solid rgba(199,214,213,0.28);
        border-radius: .65rem;
        padding: .9rem 1rem .85rem 1rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        backdrop-filter: blur(10px);
    }
    .st-key-top_nav + div {
        margin-top: 5.2rem;
    }
    [data-testid="stPageLink"] {margin-top: 0; margin-bottom: 0;}
    [data-testid="stPageLink"] a {
        justify-content: center;
        border: 1px solid rgba(199,214,213,0.22);
        border-radius: .45rem;
        padding: .7rem .8rem;
        background: rgba(109,114,117,0.22);
        color: var(--ghost-white) !important;
        text-decoration: none;
    }
    [data-testid="stPageLink"] a:hover {
        background: var(--brick-ember);
        border-color: var(--brick-ember);
        color: var(--ghost-white) !important;
    }
    [data-testid="stPageLink"] a[aria-current="page"] {
        background: var(--brick-ember);
        border-color: var(--brick-ember);
        color: var(--ghost-white) !important;
    }
    .stCaption, .small-muted {
        color: var(--ash-grey) !important;
        opacity: .78;
        font-size: .88rem;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border-color: rgba(199,214,213,0.18) !important;
    }
    .overview-panel {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 1.5rem 0 1.75rem 0;
        margin-bottom: 0;
        box-shadow: none;
    }
    .overview-panel + .overview-panel {
        border-top: 1px solid rgba(199,214,213,0.10);
    }
    .overview-panel-accent {
        border-top: none;
    }
    .st-key-overview_left_rail {
        background: rgba(109,114,117,0.055);
        border: none;
        border-right: 1px solid rgba(199,214,213,0.12);
        border-radius: 0;
        padding: 1.5rem 1.75rem 1.5rem .5rem;
        box-shadow: none;
        min-height: 100%;
    }
    .st-key-overview_left_rail h3 {
        margin-top: 0 !important;
        font-size: 1.15rem !important;
        text-transform: uppercase;
        letter-spacing: .055em !important;
        padding-bottom: .45rem;
        border-bottom: 1px solid rgba(199,214,213,0.10);
    }
    .st-key-overview_main {
        padding-left: .75rem;
    }
    .st-key-overview_main h3 {
        font-size: 1.45rem !important;
        text-transform: uppercase;
        letter-spacing: .035em !important;
        margin-top: .15rem !important;
        margin-bottom: 1rem !important;
    }
    .st-key-overview_main [data-testid="stMetric"] {
        background: rgba(109,114,117,0.10);
        border: none;
        border-top: 1px solid rgba(199,214,213,0.12);
        border-radius: 0;
    }
    .st-key-overview_main [data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }
    .st-key-overview_left_rail [data-testid="stMarkdownContainer"] p {
        line-height: 1.6;
    }
    .st-key-overview_left_rail hr {
        border-color: rgba(199,214,213,0.10) !important;
        margin: 1.5rem 0 !important;
    }
    .st-key-overview_main [data-testid="stPlotlyChart"] {
        margin-top: .35rem;
    }
    .st-key-overview_left_rail {
        position: sticky;
        top: 10rem;
        align-self: flex-start;
    }
    .st-key-overview_hero {
        padding: 1.25rem 0 1.35rem 0;
        border-top: 1px solid rgba(199,214,213,0.13);
        border-bottom: 1px solid rgba(199,214,213,0.13);
        margin-bottom: 1.4rem;
    }
    .st-key-overview_hero [data-testid="stMetric"] {
        background: transparent !important;
        border: none !important;
        border-left: 1px solid rgba(199,214,213,0.12) !important;
        padding: .35rem 1rem !important;
    }
    .st-key-overview_hero [data-testid="column"]:first-child [data-testid="stMetric"] {
        border-left: none !important;
        padding-left: 0 !important;
    }
    .st-key-overview_hero [data-testid="stMetricLabel"] {
        text-transform: uppercase;
        letter-spacing: .06em;
        font-size: .72rem !important;
        color: #C7D6D5 !important;
    }
    .st-key-overview_hero [data-testid="stMetricValue"] {
        font-size: 2.35rem !important;
        line-height: 1.05 !important;
    }
    .signal-strip {
        display: flex;
        flex-wrap: wrap;
        gap: .65rem 1.35rem;
        padding: .65rem 0 .95rem 0;
        margin-bottom: .75rem;
        border-bottom: 1px solid rgba(199,214,213,0.10);
        color: #C7D6D5;
        font-size: .78rem;
        letter-spacing: .045em;
        text-transform: uppercase;
    }
    .signal-strip strong {color: #ECEBF3; font-weight: 650;}
    .terminal-kicker {
        color: #C7D6D5;
        opacity: .78;
        font-size: .72rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-top: -.15rem;
        margin-bottom: 1.15rem;
    }
    .overview-hero-header {
        text-align: center;
        padding: 1.35rem 1rem 1.5rem 1rem;
        margin-bottom: 1.15rem;
    }
    .overview-hero-header h1 {
        margin: 0 0 .55rem 0 !important;
        font-size: clamp(2.5rem, 4.2vw, 4.4rem) !important;
        line-height: .98 !important;
        letter-spacing: -0.035em !important;
        font-weight: 700 !important;
    }
    .overview-hero-subtitle {
        max-width: 820px;
        margin: 0 auto .8rem auto;
        color: #C7D6D5;
        font-size: 1rem;
        line-height: 1.55;
        opacity: .86;
    }
    .overview-hero-meta {
        color: #C7D6D5;
        opacity: .72;
        font-size: .72rem;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .st-key-overview_refresh {
        margin: .2rem 0 1.3rem 0;
        text-align: center;
    }
    .st-key-overview_refresh [data-testid="stButton"] {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    .st-key-overview_refresh [data-testid="stButton"] > div {
        width: auto !important;
    }
    .st-key-overview_refresh button {
        width: auto !important;
        min-width: 180px;
        border-radius: 0 !important;
        border: 1px solid rgba(199,214,213,0.28) !important;
        background: transparent !important;
        color: #ECEBF3 !important;
        text-transform: uppercase;
        letter-spacing: .06em;
        font-weight: 600;
        padding: .65rem 1.15rem !important;
    }
    .st-key-overview_refresh button:hover {
        background: #C20114 !important;
        border-color: #C20114 !important;
    }
    .release-list {margin-top: .35rem;}
    .release-row {
        display: grid;
        grid-template-columns: 3.4rem 1fr;
        gap: .8rem;
        padding: .72rem 0;
        border-bottom: 1px solid rgba(199,214,213,0.08);
    }
    .release-row:first-child {
        border-top: 1px solid rgba(199,214,213,0.08);
    }
    .release-date {
        color: #ECEBF3;
        font-weight: 650;
        font-size: .82rem;
    }
    .release-name {
        color: #ECEBF3;
        font-size: .84rem;
        line-height: 1.25;
    }
    .release-type {
        display: inline-block;
        margin-top: .22rem;
        color: #C7D6D5;
        opacity: .72;
        font-size: .66rem;
        letter-spacing: .06em;
        text-transform: uppercase;
    }
    .watch-line {
        display:flex;
        justify-content:space-between;
        gap:1rem;
        padding:.42rem 0;
        border-bottom:1px solid rgba(199,214,213,0.07);
        font-size:.82rem;
    }
    .watch-line span:first-child {color:#C7D6D5;}
    .watch-line strong {color:#ECEBF3;}
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="top_nav"):
        nav = st.columns(6)
        with nav[0]:
            st.page_link("app.py", label="Overview", icon=":material/dashboard:")
        with nav[1]:
            st.page_link("pages/02_Leading.py", label="Leading", icon=":material/trending_up:")
        with nav[2]:
            st.page_link("pages/03_Coincident.py", label="Coincident", icon=":material/timeline:")
        with nav[3]:
            st.page_link("pages/04_Lagging.py", label="Lagging", icon=":material/history:")
        with nav[4]:
            st.page_link("pages/05_Indicator.py", label="Indicator", icon=":material/query_stats:")
        with nav[5]:
            st.page_link("pages/06_Data_Health.py", label="Data", icon=":material/database:")
    st.divider()


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
    category_tag={"leading":"LEI","coincident":"C","lagging":"Lag"}[category]
    heatmap_labels=table["Indicator"].astype(str) + f" ({category_tag})"
    fig=go.Figure(data=go.Heatmap(
        z=z, x=metrics, y=heatmap_labels, text=text, texttemplate="%{text}",
        zmid=0, zmin=-2, zmax=2, colorscale="RdYlGn", colorbar=dict(title="σ")
    ))
    fig.update_layout(
        template="plotly_dark",
        height=max(360, 46*len(table)),
        margin=dict(l=12,r=16,t=22,b=22),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Helvetica Neue, Arial", color="#ECEBF3"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def _composite_metrics(project_root: str, category: str):
    comp=cached_composite(project_root,category)
    if comp.empty or not comp["score"].notna().any():
        return comp, np.nan, np.nan, 0
    latest_valid = comp.loc[comp["score"].notna()].iloc[-1]
    return (
        comp,
        latest_valid["score"],
        latest_valid["positive_breadth"],
        int(latest_valid["coverage"]) if not pd.isna(latest_valid["coverage"]) else 0,
    )



def _estimated_upcoming_releases(project_root: str, limit: int = 6) -> pd.DataFrame:
    mon = get_monitor(project_root)
    today = pd.Timestamp.now().normalize()
    rows = []
    for spec in mon.registry.all():
        m = cached_metrics(project_root, spec["id"])
        if m.empty or "level" not in m or not m["level"].notna().any():
            continue
        last_obs = pd.Timestamp(m["level"].dropna().index.max()).normalize()
        freq = spec.get("frequency", "monthly")
        if freq == "daily":
            nxt = last_obs + pd.offsets.BDay(1)
            while nxt <= today:
                nxt += pd.offsets.BDay(1)
        elif freq == "weekly":
            nxt = last_obs + pd.Timedelta(days=7)
            while nxt <= today:
                nxt += pd.Timedelta(days=7)
        elif freq == "quarterly":
            nxt = last_obs + pd.DateOffset(months=3)
            while nxt <= today:
                nxt += pd.DateOffset(months=3)
        else:
            nxt = last_obs + pd.DateOffset(months=1)
            while nxt <= today:
                nxt += pd.DateOffset(months=1)
        rows.append({
            "Indicator": spec["short_name"],
            "Type": spec["category"].title(),
            "Expected": nxt,
        })
    if not rows:
        return pd.DataFrame(columns=["Indicator","Type","Expected"])
    return pd.DataFrame(rows).sort_values("Expected").head(limit)


def _latest_data_date(project_root: str) -> pd.Timestamp | None:
    latest = []
    mon = get_monitor(project_root)
    for spec in mon.registry.all():
        m = cached_metrics(project_root, spec["id"])
        if not m.empty and "level" in m and m["level"].notna().any():
            latest.append(pd.Timestamp(m["level"].dropna().index.max()))
    return max(latest) if latest else None


def _panel_start(accent: bool = False):
    klass = "overview-panel overview-panel-accent" if accent else "overview-panel"
    st.markdown(f'<div class="{klass}">', unsafe_allow_html=True)


def _panel_end():
    st.markdown('</div>', unsafe_allow_html=True)


def _overview_info_rail(project_root: str, regime: str, lb: float, lc: int, cb: float, cc: int):
    st.markdown("### Upcoming releases")
    releases = _estimated_upcoming_releases(project_root)
    if releases.empty:
        st.caption("No release estimates available.")
    else:
        rows = ['<div class="release-list">']
        for _, row in releases.iterrows():
            rows.append(
                "<div class='release-row'>"
                f"<div class='release-date'>{row['Expected'].strftime('%b %d').upper()}</div>"
                "<div>"
                f"<div class='release-name'>{row['Indicator']}</div>"
                f"<div class='release-type'>{row['Type']}</div>"
                "</div></div>"
            )
        rows.append("</div>")
        st.markdown("".join(rows), unsafe_allow_html=True)
        st.caption("Estimated from reporting frequency; exact official release timestamps will replace these later.")

    st.markdown("<div style='height:1.35rem'></div>", unsafe_allow_html=True)
    st.markdown("### What to watch")
    lead_breadth = f"{lb*100:.0f}%" if not pd.isna(lb) else "N/A"
    coinc_breadth = f"{cb*100:.0f}%" if not pd.isna(cb) else "N/A"
    st.markdown(
        "<div class='watch-line'><span>Regime</span><strong>" + regime + "</strong></div>"
        "<div class='watch-line'><span>Leading breadth</span><strong>" + lead_breadth + "</strong></div>"
        f"<div class='watch-line'><span>Leading coverage</span><strong>{lc}/10</strong></div>"
        "<div class='watch-line'><span>Coincident breadth</span><strong>" + coinc_breadth + "</strong></div>"
        f"<div class='watch-line'><span>Coincident coverage</span><strong>{cc}/4</strong></div>",
        unsafe_allow_html=True,
    )
    st.caption("Compact read of the signals and data gaps that deserve attention.")



def render_overview(project_root: str):
    setup_page("U.S. Business Cycle Monitor")
    latest_data = _latest_data_date(project_root)
    data_label = latest_data.strftime("%d %b %Y").upper() if latest_data is not None else "N/A"
    refreshed_label = pd.Timestamp.now().strftime("%d %b %Y · %H:%M").upper()
    st.markdown(
        "<section class='overview-hero-header'>"
        "<h1>U.S. Business Cycle Monitor</h1>"
        "<div class='overview-hero-subtitle'>A personal macro research terminal for leading, coincident, and lagging business-cycle evidence.</div>"
        f"<div class='overview-hero-meta'>DATA THROUGH {data_label} &nbsp;&nbsp;·&nbsp;&nbsp; SESSION REFRESH {refreshed_label}</div>"
        "</section>",
        unsafe_allow_html=True,
    )
    mon=get_monitor(project_root)
    refresh_left, refresh_center, refresh_right = st.columns([1, 0.22, 1])
    with refresh_center:
        if st.button("Refresh all data", type="primary", use_container_width=True):
            with st.spinner("Refreshing public and configured manual sources..."):
                mon.refresh_all()
                st.cache_data.clear()
            st.success("Refresh complete. Missing licensed/manual inputs remain excluded rather than fabricated.")

    lead, ls, lb, lc = _composite_metrics(project_root,"leading")
    coi, cs, cb, cc = _composite_metrics(project_root,"coincident")
    cchange = coi["score"].diff(3).dropna().iloc[-1] if not coi.empty and coi["score"].diff(3).notna().any() else np.nan
    from src.analytics.composites import classify_regime
    regime,growth,momentum=classify_regime(cs,ls,cchange)

    rail, main = st.columns([1.15, 4.85], gap="large")

    with rail:
        with st.container(key="overview_left_rail"):
            _overview_info_rail(project_root, regime, lb, lc, cb, cc)

    with main:
        with st.container(key="overview_main"):
            with st.container(key="overview_hero"):
                a,b,c,d=st.columns(4)
                a.metric("Macro regime", regime)
                b.metric(
                    "Growth",
                    f"{fmt(growth)}σ",
                    help="Current economic activity. Computed as the latest Coincident Composite score: the equal-weight average of available direction-adjusted standardized signals from payrolls, industrial production, real income ex transfers, and real manufacturing & trade sales. Positive values indicate activity running stronger than its recent historical norm; negative values indicate weaker activity."
                )
                c.metric(
                    "Momentum",
                    f"{fmt(momentum)}σ",
                    help="Forward-looking direction of the business cycle. Computed as 70% × the latest Leading Composite + 30% × the 3-month change in the Coincident Composite. Positive momentum suggests conditions are improving; negative momentum suggests deterioration."
                )
                d.metric("Latest common signal", max(lead.index.max() if not lead.empty else pd.Timestamp.min, coi.index.max() if not coi.empty else pd.Timestamp.min).strftime("%b %Y") if (not lead.empty or not coi.empty) else "N/A")

            lead_breadth_text = f"{lb*100:.0f}%" if not pd.isna(lb) else "N/A"
            coinc_breadth_text = f"{cb*100:.0f}%" if not pd.isna(cb) else "N/A"
            st.markdown(
                "<div class='signal-strip'>"
                f"<span>Leading <strong>{fmt(ls)}σ</strong></span>"
                f"<span>Coincident <strong>{fmt(cs)}σ</strong></span>"
                f"<span>Leading breadth <strong>{lead_breadth_text}</strong></span>"
                f"<span>Coincident breadth <strong>{coinc_breadth_text}</strong></span>"
                f"<span>Coverage <strong>{lc}/10 · {cc}/4</strong></span>"
                "</div>",
                unsafe_allow_html=True,
            )

            a,b=st.columns(2)
            with a:
                _panel_start()
                st.subheader("Leading")
                x,y,z=st.columns(3)
                x.metric(
                    "Composite",
                    f"{fmt(ls)}σ",
                    signal_label(ls),
                    help="Leading Composite. Each available leading indicator is transformed into its configured economic signal, standardized with a rolling 120-month Z-score using at least 36 observations, adjusted so positive generally means stronger conditions, and clipped to ±3σ. The composite is the equal-weight mean of those available signals and requires at least 7 leading indicators."
                )
                y.metric(
                    "Positive breadth",
                    f"{lb*100:.0f}%" if not pd.isna(lb) else "N/A",
                    help="Share of available leading indicators with a standardized signal above +0.25σ at the latest valid composite date. Example: 75% means three quarters of the available leading indicators are showing meaningfully positive signals."
                )
                z.metric(
                    "Coverage",
                    f"{lc}/10",
                    help="Number of leading indicators with a valid standardized signal at the same date used for the displayed composite. The leading composite requires at least 7 of the 10 configured indicators to be available."
                )
                st.plotly_chart(_heatmap(project_root,"leading"), use_container_width=True, config={"displayModeBar": False})
                st.caption(
                    "Heatmap guide: values are standardized Z-scores. Around 0 means the indicator is near its recent historical norm; "
                    "+0.25 to +1.0 suggests moderately positive conditions; above +1.0 is unusually strong; "
                    "-0.25 to -1.0 suggests moderately negative conditions; below -1.0 is unusually weak. "
                    "Signal shows the indicator's current standardized economic reading after direction adjustment. "
                    "Momentum shows whether that underlying signal has been improving or deteriorating over roughly the last three months. "
                    "For most leading and coincident indicators, greener/positive values are stronger and redder/negative values are weaker."
                )
                _panel_end()
            with b:
                _panel_start()
                st.subheader("Coincident")
                x,y,z=st.columns(3)
                x.metric(
                    "Composite",
                    f"{fmt(cs)}σ",
                    signal_label(cs),
                    help="Coincident Composite. Each available coincident indicator is transformed into its configured economic signal, standardized with a rolling 120-month Z-score using at least 36 observations, direction-adjusted, and clipped to ±3σ. The composite is the equal-weight mean of the available signals and requires at least 3 of the 4 coincident indicators."
                )
                y.metric(
                    "Positive breadth",
                    f"{cb*100:.0f}%" if not pd.isna(cb) else "N/A",
                    help="Share of available coincident indicators with a standardized signal above +0.25σ at the latest valid composite date. Higher breadth means strength is spread across more parts of current economic activity rather than being driven by only one series."
                )
                z.metric(
                    "Coverage",
                    f"{cc}/4",
                    help="Number of coincident indicators with a valid standardized signal at the same date used for the displayed composite. The coincident composite requires at least 3 of the 4 configured indicators to be available."
                )
                st.plotly_chart(_heatmap(project_root,"coincident"), use_container_width=True, config={"displayModeBar": False})
                st.caption(
                    "Heatmap guide: values are standardized Z-scores. Around 0 means the indicator is near its recent historical norm; "
                    "+0.25 to +1.0 suggests moderately positive conditions; above +1.0 is unusually strong; "
                    "-0.25 to -1.0 suggests moderately negative conditions; below -1.0 is unusually weak. "
                    "Signal shows the indicator's current standardized economic reading after direction adjustment. "
                    "Momentum shows whether that underlying signal has been improving or deteriorating over roughly the last three months. "
                    "For most leading and coincident indicators, greener/positive values are stronger and redder/negative values are weaker."
                )
                _panel_end()

    _panel_start()
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
    fig.update_layout(
        template="plotly_dark",
        height=450,
        margin=dict(l=18,r=18,t=18,b=18),
        legend=dict(orientation="h"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Helvetica Neue, Arial", color="#ECEBF3"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(199,214,213,0.16)", tickfont=dict(color="#C7D6D5"))
    fig.update_yaxes(gridcolor="rgba(199,214,213,0.08)", zerolinecolor="rgba(199,214,213,0.16)", tickfont=dict(color="#C7D6D5"))
    xmax_candidates=[]
    if not lead.empty:
        xmax_candidates.append(lead.index.max())
    if not coi.empty:
        xmax_candidates.append(coi.index.max())
    if xmax_candidates:
        fig.update_xaxes(range=[DEFAULT_CHART_START, max(xmax_candidates)])
    st.plotly_chart(fig,use_container_width=True, config={"displayModeBar": False})
    _panel_end()

    _panel_start()
    st.subheader("Lagging conditions")
    lag=_category_table(project_root,"lagging")
    st.dataframe(lag[["Indicator","Level","YoY %","Momentum","Data"]], use_container_width=True, hide_index=True)
    _panel_end()


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
        st.plotly_chart(line_chart(comp["score"].dropna(), f"{title} composite", recession, zero_line=True),use_container_width=True, config={"displayModeBar": False})
        st.subheader("Current signal heatmap")
        st.plotly_chart(_heatmap(project_root,category),use_container_width=True, config={"displayModeBar": False})
        st.caption(
            "Heatmap guide: values are standardized Z-scores. Around 0 means the indicator is near its recent historical norm; "
            "+0.25 to +1.0 suggests moderately positive conditions; above +1.0 is unusually strong; "
            "-0.25 to -1.0 suggests moderately negative conditions; below -1.0 is unusually weak. "
            "Signal is the current standardized reading after any economic direction adjustment. Momentum measures the recent change "
            "in the underlying signal over roughly three months. For leading and coincident indicators, positive values generally mean stronger conditions."
        )
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
    category_label = {
        "leading": "Leading Indicator",
        "coincident": "Coincident Indicator",
        "lagging": "Lagging Indicator",
    }.get(spec.get("category"), str(spec.get("category","")).title())
    st.markdown(f"**Type:** {category_label}")
    st.markdown("### What it is")
    st.write(spec.get("description",""))
    st.markdown("### Why it matters")
    st.write(spec.get("why_it_matters",""))
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
    scale=st.radio("Y-axis scale",["Robust","Full"],horizontal=True,help="Robust zooms to the normal historical range without changing the underlying data. Full shows every extreme observation.")
    yrs=st.select_slider("History",options=[3,5,10,20,40],value=10)
    series=m[metric].dropna()
    cutoff=series.index.max()-pd.DateOffset(years=yrs) if not series.empty else None
    if cutoff is not None: series=series[series.index>=cutoff]
    st.plotly_chart(line_chart(
        series,
        metric.replace("_"," ").title(),
        _recession(project_root),
        zero_line=metric in {"yoy_pct","growth_3m_ann","growth_6m_ann","signal","momentum"},
        start_at_data=True,
        robust_y=scale=="Robust",
    ),use_container_width=True, config={"displayModeBar": False})
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
