"""Economic themes and concise research notes for the personal terminal."""
from __future__ import annotations
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

from src.analytics.interpretations import indicator_reading

COLORS = ["#C7D6D5", "#8FAABF", "#C9AA78", "#A69CB5", "#6D7275"]


def load_sections(project_root):
    return yaml.safe_load((Path(project_root) / "config" / "economic_sections.yaml").read_text(encoding="utf-8"))["sections"]


def theme_chart(section, specs, metrics):
    fig = go.Figure()
    dates = [m.index.max() for m in metrics.values() if not m.empty]
    end = max(dates) if dates else pd.Timestamp.now()
    start = end - pd.DateOffset(years=5)
    for number, key in enumerate(section["indicators"]):
        frame = metrics[key]
        if frame.empty or "signal" not in frame:
            continue
        series = frame["signal"].loc[frame.index >= start]
        if not series.notna().any():
            continue
        fig.add_trace(go.Scatter(
            x=series.index, y=series, name=specs[key]["short_name"],
            mode="lines", connectgaps=False,
            line=dict(color=COLORS[number % len(COLORS)], width=1.8),
            hovertemplate="%{y:.2f}σ<extra>%{fullData.name}</extra>",
        ))
    fig.add_hline(y=0, line_color="rgba(199,214,213,.35)", line_dash="dot", line_width=1)
    fig.update_layout(
        height=195, margin=dict(l=5, r=5, t=8, b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial", color="#C7D6D5", size=10),
        hovermode="x unified", legend=dict(orientation="h", y=1.02, yanchor="bottom", font=dict(size=10)),
    )
    fig.update_xaxes(range=[start, end], showgrid=False, zeroline=False, tickformat="%Y")
    fig.update_yaxes(range=[-3.2, 3.2], tickvals=[-3, 0, 3], ticksuffix="σ", gridcolor="rgba(199,214,213,.07)", zeroline=False)
    return fig


def render_reading(spec, metrics):
    reading = indicator_reading(spec, metrics)
    if reading["date"] is not None:
        st.caption(f"{reading['date'].strftime('%b %Y')} · {spec['category'].title()} · {reading['state']}")
    st.write(reading["text"])
    if reading["qualification"]:
        st.caption(reading["qualification"])


def render_economic_overview(project_root, registry, metric_loader):
    sections = load_sections(project_root)
    specs = {spec["id"]: spec for spec in registry}
    metrics = {key: metric_loader(project_root, key) for key in specs}
    st.markdown("<div class='research-intro'><div class='research-eyebrow'>ECONOMIC OVERVIEW</div>"
                "<h2>Read the economy, channel by channel.</h2>"
                "<p>Current activity, the future pipeline and the conditions that connect them.</p></div>", unsafe_allow_html=True)
    for offset in range(0, len(sections), 2):
        columns = st.columns(2, gap="large")
        for position, section in enumerate(sections[offset:offset + 2]):
            with columns[position]:
                with st.container(key=f"theme_{section['id']}"):
                    st.markdown(
                        f"<div class='theme-heading'><span class='theme-number'>{offset + position + 1:02d}</span>"
                        f"<h4>{escape(section['title'])}</h4></div>"
                        f"<div class='theme-question'>{escape(section['question'])}</div>", unsafe_allow_html=True)
                    rows = []
                    available = 0
                    for key in section["indicators"]:
                        reading = indicator_reading(specs[key], metrics[key])
                        available += reading["signal"] is not None
                        value = f"{reading['signal']:+.2f}σ" if reading["signal"] is not None else "N/A"
                        date = reading["date"].strftime("%b %y") if reading["date"] is not None else "No data"
                        rows.append(f"<div class='theme-observation'><span>{escape(specs[key]['short_name'])}</span>"
                                    f"<span class='theme-date'>{date}</span><strong>{value}</strong></div>")
                    st.markdown("<div class='theme-evidence'>" + "".join(rows) + "</div>", unsafe_allow_html=True)
                    if available:
                        st.plotly_chart(theme_chart(section, specs, metrics), use_container_width=True, config={"displayModeBar": False}, key=f"chart_{section['id']}")
                    else:
                        st.caption("Historical signals will appear when sufficient observations are available.")
                    st.caption(f"Five-year signal history · {available}/{len(section['indicators'])} current standardized readings")
                    primary = section["indicators"][0]
                    brief = indicator_reading(specs[primary], metrics[primary])
                    st.markdown(f"<div class='theme-brief'><span>{escape(specs[primary]['short_name'])}</span>"
                                f"<p>{escape(brief['text'])}</p></div>", unsafe_allow_html=True)
                    with st.expander("Interpretation & transmission", expanded=False):
                        st.write(section["mechanism"])
                        st.caption(section["qualification"])
                        for key in section["indicators"]:
                            st.markdown(f"**{specs[key]['name']}**")
                            render_reading(specs[key], metrics[key])
    st.caption("Signals compare each indicator's configured transformation with its own rolling historical norm. They are not raw growth rates or theme composites. Dates can differ across indicators; inflation, borrowing costs and loan balances are contextual rather than good/bad scores.")
    with st.expander("Cycle anatomy · connect the channels", expanded=False):
        st.markdown("#### From intentions to activity")
        st.write("Orders and permits describe the pipeline. Production and real sales show how much activity is occurring. Firms can adjust hours before headcount, while employment and real income influence households' purchasing power. Inventories relative to sales help reveal whether production is matching demand. These relationships can overlap and do not follow a fixed timetable.")
        st.markdown("#### The financial feedback")
        st.write("Inflation and productivity shape cost pressure. Policy and financial conditions influence the price and availability of credit, which feeds back into housing, investment and spending. Market prices anticipate these developments but also respond to discount rates and risk appetite.")
        st.markdown("#### Read agreement and divergence")
        st.write("Compare the investment pipeline with current production; hours and claims with payrolls; income with sentiment and orders; and financial conditions with credit outstanding. Agreement adds breadth to the interpretation. Divergence identifies a relationship to investigate, rather than establishing a turning point by itself.")
        st.page_link("pages/05_Indicator.py", label="Open indicator research")
