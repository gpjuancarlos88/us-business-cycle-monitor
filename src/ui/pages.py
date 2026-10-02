from __future__ import annotations
from pathlib import Path
from html import escape
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app_core import MacroMonitor
from src.data_sources.releases import ReleaseCalendar, upcoming_releases
from src.charts.timeseries import DEFAULT_CHART_START, line_chart
from src.ui.helpers import fmt, signal_label
from src.ui.research import render_economic_overview, render_reading, render_cross_indicator_research, render_economic_tensions, chapter_header, concise_text
from src.charts.palette import indicator_color
from src.charts.terminal import terminal_chart
from src.ui.overview import apply_overview_style, render_terminal_header, render_chapter_navigation, render_terminal_footer

def get_monitor(project_root: str):
    return MacroMonitor(project_root)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_metrics(project_root: str, indicator_id: str):
    return get_monitor(project_root).metrics(indicator_id)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_composite(project_root: str, category: str):
    return get_monitor(project_root).category_composite(category)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_raw(project_root: str, indicator_id: str):
    mon = get_monitor(project_root)
    raw = mon.repo.load(indicator_id)
    return mon.manager.refresh(indicator_id) if raw.empty else raw


def setup_page(title: str, *, overview: bool = False):
    st.set_page_config(page_title=title, page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
    page_css = """
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
    .release-name a {color: #ECEBF3; text-decoration: none;}
    .release-name a:hover {text-decoration: underline;}
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

    .research-intro {margin-top:2.8rem; padding:1.75rem 1rem 1.2rem; border-top:1px solid rgba(199,214,213,.28); border-bottom:1px solid rgba(199,214,213,.09); background:linear-gradient(90deg,rgba(109,114,117,.09),rgba(12,18,12,0)); margin-bottom:1rem;}
    .chapter-number {font-variant-numeric:tabular-nums; color:#ECEBF3; margin-right:.2rem;}
    .series-marker {display:inline-block; width:.38rem; height:.38rem; border-radius:50%; margin-right:.45rem; vertical-align:middle;}
    .st-key-economic_tensions {padding:1.2rem 0 1.4rem;}
    .tension-heading {font-size:1.3rem; color:#ECEBF3; font-weight:550; margin-bottom:.45rem;}
    .st-key-economic_tensions [data-testid="stExpander"] {border-radius:0; border-color:rgba(199,214,213,.12);}
    .st-key-indicator_analyst_reading {border-top:1px solid rgba(199,214,213,.18); padding:1rem 0;}
    .research-eyebrow {color:#C7D6D5; font-size:.68rem; letter-spacing:.16em; margin-bottom:.7rem;}
    .research-intro h2 {font-size:clamp(1.5rem,2.2vw,2.3rem) !important; margin:0 0 .55rem !important;}
    .research-intro p {color:#C7D6D5 !important; opacity:.8; font-size:.93rem;}
    [class*="st-key-theme_"] {padding:1.35rem 0 1.1rem; border-top:1px solid rgba(199,214,213,.16); border-radius:0;}
    .theme-heading {display:flex; align-items:baseline; gap:.9rem; margin-bottom:.3rem;}
    .theme-number {font-size:.72rem; color:#6D7275; letter-spacing:.08em;}
    .theme-heading h4 {font-size:1.25rem !important; font-weight:600; padding:0 !important; margin:0 !important;}
    .theme-question {color:#C7D6D5; font-size:.84rem; margin-bottom:1rem; opacity:.8;}
    .theme-evidence {min-height:9.6rem;}
    .theme-observation {display:grid; grid-template-columns:minmax(0,1fr) 4.6rem 4.5rem; gap:.55rem; align-items:baseline; border-bottom:1px solid rgba(199,214,213,.07); padding:.38rem 0; font-size:.8rem;}
    .theme-observation strong {text-align:right; font-variant-numeric:tabular-nums; color:#ECEBF3; font-weight:550;}
    .theme-brief {padding:.75rem 0 .65rem; min-height:5.8rem;}
    .theme-brief > span {font-size:.66rem; color:#C7D6D5; letter-spacing:.08em; text-transform:uppercase;}
    .theme-brief p {font-size:.83rem !important; line-height:1.6; margin:.4rem 0 0; color:#C7D6D5 !important;}
    .theme-date {text-align:right; color:#C7D6D5; opacity:.55; font-size:.66rem; text-transform:uppercase;}
    [class*="st-key-theme_"] [data-testid="stExpander"] {border:1px solid rgba(199,214,213,.12); border-radius:0;}
    [class*="st-key-theme_"] [data-testid="stPlotlyChart"] {margin-top:.5rem;}
    .st-key-comparison_workspace {padding:1.25rem 0 1.75rem; border-top:1px solid rgba(199,214,213,.16);}
    .comparison-question {font-size:1.2rem; font-weight:550; margin:.8rem 0 .35rem; color:#ECEBF3;}
    .comparison-value {font-size:2rem; font-weight:550; letter-spacing:-.03em; line-height:1.2; color:#ECEBF3; font-variant-numeric:tabular-nums;}
    .comparison-value > span {font-size:1rem; margin-left:.25rem; opacity:.65;}
    .comparison-reading {border-left:2px solid #C7D6D5; padding:.9rem 1.1rem; margin:.75rem 0; background:rgba(109,114,117,.065);}
    .comparison-reading .research-eyebrow {margin-bottom:.45rem; letter-spacing:.08em;}
    .comparison-reading p {font-size:.92rem; line-height:1.65; margin:0;}
    .st-key-comparison_workspace [data-testid="stExpander"] {border-radius:0; border-color:rgba(199,214,213,.12);}
    @media (max-width:800px) {
        .theme-evidence {min-height:0;}
        .research-intro {margin-top:1.5rem; padding:1.35rem .75rem 1rem;}
        .theme-observation {font-size:.74rem;}
        .st-key-overview_left_rail {position:static; padding-right:.7rem;}
    }
    </style>
    """
    if overview:
        st.html(page_css)
        apply_overview_style()
    else:
        st.markdown(page_css, unsafe_allow_html=True)
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
    if not overview:
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


def _heatmap(project_root: str, category: str, *, terminal: bool = False):
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
    if terminal:
        fig.update_traces(colorscale=[[0,"#944D58"],[.25,"#67434F"],[.5,"#182B36"],[.75,"#367768"],[1,"#69B6A3"]],
                          xgap=5, ygap=5, textfont=dict(family="Consolas, monospace",size=12,color="#E3EDF2"),
                          hovertemplate="%{y}<br>%{x}: %{z:.2f}σ<extra></extra>",
                          colorbar=dict(title="σ",thickness=8,len=.7,outlinewidth=0))
        terminal_chart(fig)
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



@st.cache_data(ttl=3600, show_spinner=False)
def cached_release_calendar(project_root: str, _force=False):
    return ReleaseCalendar(project_root).load(force=_force)


def _upcoming_releases(project_root: str, limit=None):
    events, status = cached_release_calendar(project_root)
    return upcoming_releases(events, get_monitor(project_root).registry.all(), limit=limit), status


def _latest_data_date(project_root: str) -> pd.Timestamp | None:
    latest = []
    mon = get_monitor(project_root)
    for spec in mon.registry.all():
        raw = cached_raw(project_root, spec["id"])
        if not raw.empty and raw["observation_date"].notna().any():
            latest.append(pd.Timestamp(raw["observation_date"].max()))
    return max(latest) if latest else None


def _overview_releases(project_root: str):
    st.markdown("<div class='briefing-title'>BRIEFING / RELEASE CALENDAR</div>", unsafe_allow_html=True)
    st.markdown("### Upcoming official releases")
    releases, status = _upcoming_releases(project_root, limit=6)
    if releases.empty:
        st.caption("No upcoming official dates available for the mapped indicators.")
    else:
        rows = ['<div class="release-list">']
        for _, row in releases.iterrows():
            when = row["Release time (ET)"]
            clock = when.strftime("%H:%M ET") if row["Time known"] else "Time not published"
            rows.append(
                "<div class='release-row'>"
                f"<div class='release-date'>{when.strftime('%b %d').upper()}</div>"
                "<div>"
                f"<div class='release-name'><a href='{escape(row['Source'], quote=True)}' "
                f"target='_blank' rel='noopener noreferrer'>{escape(row['Indicators'])}</a></div>"
                f"<div class='release-type'>{escape(row['Agency'])} · {clock} · {escape(row['Categories'])}</div>"
                "</div></div>"
            )
        rows.append("</div>")
        st.markdown("".join(rows), unsafe_allow_html=True)
    st.caption("Official schedules · U.S. Eastern time. Dates may change; FRED availability can follow the agency release.")
    if status["Status"].isin(["Unavailable", "Cached · refresh failed"]).any():
        st.caption("Some calendar feeds could not refresh. See Data for source status and cached timestamps.")

def _overview_watch(regime: str, lb: float, lc: int, cb: float, cc: int):
    st.markdown("<div class='briefing-title'>BRIEFING / SIGNAL COVERAGE</div>", unsafe_allow_html=True)
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



def _overview_cycle_panel(project_root, category, score, breadth, coverage):
    is_leading = category == "leading"
    title = "Leading" if is_leading else "Coincident"
    total, minimum = (10, 7) if is_leading else (4, 3)
    role = "Forward pipeline" if is_leading else "Current activity"
    st.markdown(f"<div class='briefing-title'>{role.upper()} / {total} INDICATORS</div>", unsafe_allow_html=True)
    st.subheader(title)
    x, y, z = st.columns(3)
    x.metric("Composite", f"{fmt(score)}σ",
             help=f"{title} Composite: equal-weight mean of available direction-adjusted signals. Each indicator uses its configured economic transformation, a rolling 120-month Z-score with at least 36 observations, and clipping to ±3σ. At least {minimum} of {total} components are required.")
    position = "Unavailable" if pd.isna(score) else "Above historical norm" if score > .25 else "Below historical norm" if score < -.25 else "Near historical norm"
    x.caption(position)
    y.metric("Positive breadth", f"{breadth*100:.0f}%" if not pd.isna(breadth) else "N/A",
             help="Share of available indicators with a standardized signal above +0.25σ at the displayed composite date. Higher breadth means strength is spread across more indicators.")
    z.metric("Coverage", f"{coverage}/{total}",
             help=f"Number of valid component signals at the composite reading date; minimum {minimum}/{total} required.")
    st.plotly_chart(_heatmap(project_root, category, terminal=True), use_container_width=True, config={"displayModeBar": False}, key=f"overview_heatmap_{category}")
    st.caption("Signal = historical position · Momentum = standardized recent change")
    with st.expander("How to read the heatmap", expanded=False):
        st.write("Values are standardized Z-scores after economic direction adjustment. Zero is the rolling historical norm. Above +0.25σ is meaningfully positive and below −0.25σ is meaningfully negative; readings beyond ±1σ are unusually strong or weak relative to history. Green tones indicate stronger signals, rose tones weaker signals, and dark cells the neutral region. Missing cells have no valid reading.")
        st.caption("Momentum is a standardized change statistic. Its sign alone does not establish that the underlying economic measure has risen or fallen; use the analyst readings for the exact three-month comparison.")


def render_overview(project_root: str):
    setup_page("U.S. Business Cycle Monitor", overview=True)
    mon = get_monitor(project_root)
    latest_data = _latest_data_date(project_root)
    data_label = latest_data.strftime("%d %b %Y").upper() if latest_data is not None else "N/A"
    session_label = pd.Timestamp.now(tz="UTC").strftime("%d %b %Y / %H:%M").upper()
    render_terminal_header(data_label, session_label)
    with st.container(key="overview_refresh"):
        if st.button("Refresh all data", type="primary"):
            with st.spinner("Refreshing public and configured manual sources..."):
                mon.refresh_all()
                st.cache_data.clear()
            st.session_state["overview_refresh_complete"] = True
            st.rerun()
    if st.session_state.pop("overview_refresh_complete", False):
        st.success("Refresh complete. See Data for source availability; missing licensed/manual inputs remain excluded.")

    lead, ls, lb, lc = _composite_metrics(project_root, "leading")
    coi, cs, cb, cc = _composite_metrics(project_root, "coincident")
    cchange = coi["score"].diff(3).dropna().iloc[-1] if not coi.empty and coi["score"].diff(3).notna().any() else np.nan
    from src.analytics.composites import classify_regime
    regime, growth, momentum = classify_regime(cs, ls, cchange)
    composite_dates = [frame.loc[frame["score"].notna()].index.max() for frame in [lead, coi]
                       if not frame.empty and frame["score"].notna().any()]
    with st.container(key="overview_hero"):
        a, b, c, d = st.columns(4)
        a.metric("Macro regime", regime)
        b.metric("Growth", f"{fmt(growth)}σ",
                 help="Current activity: the latest Coincident Composite, averaging valid direction-adjusted standardized payrolls, production, real income and real sales signals. Positive is stronger than its rolling historical norm, not a GDP growth rate.")
        c.metric("Momentum", f"{fmt(momentum)}σ",
                 help="70% × latest Leading Composite + 30% × the exact three-month change in the Coincident Composite. This standardized cycle statistic is distinct from each indicator's underlying economic direction.")
        d.metric("Latest composite month", max(composite_dates).strftime("%b %Y") if composite_dates else "N/A",
                 help="Most recent valid month across the leading and coincident composites. Their individual reading months can differ; this is not a shared-month comparison.")
    leading_breadth = f"{lb*100:.0f}%" if not pd.isna(lb) else "N/A"
    coincident_breadth = f"{cb*100:.0f}%" if not pd.isna(cb) else "N/A"
    st.markdown(
        "<div class='signal-strip'>"
        f"<span>Leading <strong>{fmt(ls)}σ</strong></span>"
        f"<span>Coincident <strong>{fmt(cs)}σ</strong></span>"
        f"<span>Leading breadth <strong>{leading_breadth}</strong></span>"
        f"<span>Coincident breadth <strong>{coincident_breadth}</strong></span>"
        f"<span>Coverage <strong>{lc}/10 · {cc}/4</strong></span></div>", unsafe_allow_html=True,
    )
    with st.container(key="overview_briefing"):
        releases, watch = st.columns([2.5, 1], gap="large")
        with releases:
            _overview_releases(project_root)
        with watch:
            _overview_watch(regime, lb, lc, cb, cc)
    render_chapter_navigation()

    render_economic_overview(project_root, mon.registry.all(), cached_metrics, cached_raw)
    render_cross_indicator_research(project_root, mon.registry.all(), cached_metrics)
    render_economic_tensions(project_root, cached_metrics, cached_composite)
    chapter_header(4, "CYCLE EVIDENCE", "Timing, breadth and confirmation.", "The leading and coincident lenses behind the macro regime.")
    leading_panel, coincident_panel = st.columns(2, gap="large")
    with leading_panel:
        with st.container(key="overview_leading"):
            _overview_cycle_panel(project_root, "leading", ls, lb, lc)
    with coincident_panel:
        with st.container(key="overview_coincident"):
            _overview_cycle_panel(project_root, "coincident", cs, cb, cc)

    chapter_header(5, "COMPOSITE HISTORY", "The cycle through time.", "Leading and coincident evidence against the recession record.")
    with st.container(key="overview_history"):
        recession=_recession(project_root)
        fig=go.Figure()
        if not lead.empty: fig.add_trace(go.Scatter(x=lead.index,y=lead["score"],name="Leading",mode="lines",line=dict(color=indicator_color("leading_composite"))))
        if not coi.empty: fig.add_trace(go.Scatter(x=coi.index,y=coi["score"],name="Coincident",mode="lines",line=dict(color=indicator_color("coincident_composite"))))
        if not recession.empty:
            active=recession[recession.index >= DEFAULT_CHART_START].fillna(0).astype(int); start=None
            for dt,val in active.items():
                if val==1 and start is None: start=dt
                elif val==0 and start is not None:
                    fig.add_vrect(x0=start,x1=dt,fillcolor="#6D7275",opacity=.22,line_width=0,layer="below"); start=None
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
        window = st.radio("History window", ["5Y", "10Y", "20Y", "Full"], index=1, horizontal=True, key="overview_history_window")
        if xmax_candidates:
            end = max(xmax_candidates)
            start = DEFAULT_CHART_START if window == "Full" else max(DEFAULT_CHART_START, end-pd.DateOffset(years=int(window[:-1])))
            fig.update_xaxes(range=[start, end])
        st.plotly_chart(terminal_chart(fig),use_container_width=True, config={"displayModeBar": False})
        st.caption("Zero marks the historical-norm reference. Grey bands show NBER recessions. Watch direction and divergence.")
        with st.expander("How to read composite history", expanded=False):
            st.caption(
                "How to read this chart: the Leading Composite summarizes forward-looking indicators and is intended to turn before the broader economy, "
                "while the Coincident Composite summarizes indicators that move more closely with current economic activity. Values are standardized scores: "
                "readings above 0 indicate conditions stronger than their recent historical norm and readings below 0 indicate weaker conditions. "
                "The dashed zero line is the neutral reference point. Grey recession bands show NBER-dated recessions. "
                "The most useful information is often in the direction and divergence of the two lines—for example, a falling Leading Composite while the "
                "Coincident Composite remains positive can signal that current growth is still intact but forward momentum is deteriorating."
            )

    chapter_header(6, "LAGGING CONDITIONS", "Confirmation and accumulated pressure.", "Labor duration, inventories, costs and credit after the cycle has moved.")
    with st.container(key="overview_diagnostics"):
        lag = _category_table(project_root, "lagging")
        st.dataframe(lag[["Indicator", "Level", "YoY %", "Momentum", "Data"]], use_container_width=True, hide_index=True,
                     column_config={"Level":st.column_config.NumberColumn(format="%.2f"),
                                    "YoY %":st.column_config.NumberColumn(format="%.2f%%"),
                                    "Momentum":st.column_config.NumberColumn(format="%.2f")})
        st.caption("Diagnostic readings · contextual costs and credit are not assigned a single good/bad score.")
    registry = mon.registry.all()
    render_terminal_footer(sum(s["category"] != "context" for s in registry), sum(s["category"] == "context" for s in registry))


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
        st.plotly_chart(line_chart(comp["score"].dropna(), f"{title} composite", recession, zero_line=True, indicator_id=f"{category}_composite"),use_container_width=True, config={"displayModeBar": False})
        st.subheader("Current signal heatmap")
        st.plotly_chart(_heatmap(project_root,category),use_container_width=True, config={"displayModeBar": False})
        st.caption("Signal = historical position · Momentum = standardized recent change · hover for values")
        with st.expander("How to read the heatmap", expanded=False):
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
    c.metric("Signal",f"{fmt(row.get('signal'))}σ","Contextual" if spec.get("direction") == 0 else signal_label(row.get("signal")))
    d.metric("Momentum",f"{fmt(row.get('momentum'))}σ")
    with st.container(key="indicator_analyst_reading"):
        st.subheader("Analyst reading")
        render_reading(spec, m, compact=True)
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
        indicator_id=spec["id"],
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
    st.subheader("Official release calendar")
    if st.button("Refresh release calendars"):
        cached_release_calendar.clear()
        cached_release_calendar(project_root, _force=True)
    releases, calendar_status = _upcoming_releases(project_root)
    st.caption("BLS, BEA and Census schedules. All release times use U.S. Eastern time, including daylight saving changes. These are publication dates, separate from observation dates and FRED ingestion.")
    if releases.empty:
        st.info("No upcoming official releases found for the mapped indicators.")
    else:
        display = releases.drop(columns=["Time known"]).copy()
        display["Release time (ET)"] = [
            when.strftime("%Y-%m-%d %H:%M %Z") if known else when.strftime("%Y-%m-%d") + " · time not published"
            for when, known in zip(releases["Release time (ET)"], releases["Time known"])
        ]
        st.dataframe(display, use_container_width=True, hide_index=True,
                     column_config={"Source": st.column_config.LinkColumn("Source")})
    st.dataframe(calendar_status, use_container_width=True, hide_index=True,
                 column_config={"Source": st.column_config.LinkColumn("Source")})
    st.caption("Coverage currently includes Employment Situation, CPI, Productivity and Costs, Personal Income and Outlays, factory orders, durable goods, housing permits and business inventories. Other indicators remain unscheduled here; no frequency-based dates are presented as official releases.")
    st.subheader("Update log")
    st.dataframe(mon.repo.recent_logs(),use_container_width=True,hide_index=True)
    st.info("For ISM New Orders, place a CSV with columns date,value at data/manual/ism_new_orders.csv, then refresh. This keeps proprietary/licensed data explicit rather than scraping an unofficial source.")
