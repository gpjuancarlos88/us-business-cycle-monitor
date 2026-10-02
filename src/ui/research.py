"""Economic themes and concise research notes for the personal terminal."""
from __future__ import annotations
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

from src.analytics.interpretations import indicator_reading
from src.charts.palette import indicator_color
from src.charts.terminal import terminal_chart
from src.ui.policy import render_inflation, render_policy_rates

def chapter_header(number, label, title, subtitle):
    st.markdown(f"<div class='research-intro' id='chapter-{number:02d}'><div class='research-eyebrow'><span class='chapter-number'>{number:02d}</span> / {escape(label)}</div>"
                f"<h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>", unsafe_allow_html=True)


def concise_text(text):
    sentences = text.split(". ")
    if len(sentences) <= 2:
        return text
    direction = next((sentence for sentence in sentences[1:] if "versus three months" in sentence or "Over three months" in sentence or "Both underlying" in sentence), sentences[1])
    return sentences[0] + ". " + direction.rstrip(".") + "."


def load_sections(project_root):
    return yaml.safe_load((Path(project_root) / "config" / "economic_sections.yaml").read_text(encoding="utf-8"))["sections"]


def theme_chart(section, specs, metrics):
    fig = go.Figure()
    dates = [m.index.max() for m in metrics.values() if not m.empty]
    end = max(dates) if dates else pd.Timestamp.now()
    start = end - pd.DateOffset(years=5)
    for key in section["indicators"]:
        frame = metrics[key]
        if frame.empty or "signal" not in frame:
            continue
        series = frame["signal"].loc[frame.index >= start]
        if not series.notna().any():
            continue
        fig.add_trace(go.Scatter(
            x=series.index, y=series, name=specs[key]["short_name"],
            mode="lines", connectgaps=False,
            line=dict(color=indicator_color(key), width=1.8),
            hovertemplate="%{y:.2f}σ<extra>%{fullData.name}</extra>",
        ))
    fig.add_hline(y=0, line_color="rgba(199,214,213,.35)", line_dash="dot", line_width=1)
    fig.update_layout(
        height=195, margin=dict(l=5, r=5, t=8, b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial", color="#C7D6D5", size=10),
        hovermode="x unified", legend=dict(orientation="h", y=1.02, yanchor="bottom", font=dict(size=10)),
    )
    fig.update_xaxes(range=[start, end], showgrid=False, zeroline=False, tickformat="%Y", dtick="M12")
    fig.update_yaxes(range=[-3.2, 3.2], tickvals=[-3, 0, 3], ticksuffix="σ", gridcolor="rgba(199,214,213,.07)", zeroline=False)
    return terminal_chart(fig)


def render_reading(spec, metrics, compact=False):
    reading = indicator_reading(spec, metrics)
    if reading["date"] is not None:
        st.caption(f"{reading['date'].strftime('%b %Y')} · {spec['category'].title()} · {reading['state']}")
    summary = concise_text(reading["text"])
    if spec.get("policy_reference") is not None or spec.get("comparison_reference") is not None:
        summary = ". ".join(reading["text"].split(". ")[:2]).rstrip(".") + "."
    st.write(summary if compact else reading["text"])
    if compact:
        with st.expander("Reading details & qualifications", expanded=False):
            st.write(reading["text"])
            st.caption(reading["qualification"])
    elif reading["qualification"]:
        st.caption(reading["qualification"])


def render_economic_overview(project_root, registry, metric_loader, raw_loader=None):
    sections = load_sections(project_root)
    specs = {spec["id"]: spec for spec in registry}
    metrics = {key: metric_loader(project_root, key) for key in specs}
    chapter_header(1, "ECONOMIC OVERVIEW", "Read the economy, channel by channel.", "Current activity, the future pipeline and the conditions that connect them.")
    for offset in range(0, len(sections), 2):
        columns = st.columns(2, gap="large")
        for position, section in enumerate(sections[offset:offset + 2]):
            with columns[position]:
                with st.container(key=f"theme_{section['id']}"):
                    st.markdown(
                        f"<div class='theme-heading'><span class='theme-number'>{offset + position + 1:02d}</span>"
                        f"<h4>{escape(section['title'])}</h4></div>"
                        f"<div class='theme-question'>{escape(section['question'])}</div>", unsafe_allow_html=True)
                    if section["id"] == "inflation":
                        render_inflation(specs, metrics)
                        with st.expander("Services & manufacturing cost detail", expanded=False):
                            for key in ["services_inflation", "unit_labor_costs"]:
                                st.markdown(f"**{specs[key]['name']}**")
                                render_reading(specs[key], metrics[key])
                        continue
                    chart_section = dict(section, indicators=[key for key in section["indicators"] if specs[key].get("context_type") != "rates"])
                    rows = []
                    available = 0
                    for key in chart_section["indicators"]:
                        reading = indicator_reading(specs[key], metrics[key])
                        available += reading["signal"] is not None
                        value = f"{reading['signal']:+.2f}σ" if reading["signal"] is not None else "N/A"
                        date = reading["date"].strftime("%b %y") if reading["date"] is not None else "No data"
                        rows.append(f"<div class='theme-observation'><span><i class='series-marker' style='background:{indicator_color(key)}'></i>{escape(specs[key]['short_name'])}</span>"
                                    f"<span class='theme-date'>{date}</span><strong>{value}</strong></div>")
                    st.markdown("<div class='theme-evidence'>" + "".join(rows) + "</div>", unsafe_allow_html=True)
                    if available:
                        st.plotly_chart(theme_chart(chart_section, specs, metrics), use_container_width=True, config={"displayModeBar": False}, key=f"chart_{section['id']}")
                    else:
                        st.caption("Historical signals will appear when sufficient observations are available.")
                    st.caption(f"Five-year signal history · {available}/{len(chart_section['indicators'])} current standardized readings")
                    primary = section["indicators"][0]
                    brief = indicator_reading(specs[primary], metrics[primary])
                    st.markdown(f"<div class='theme-brief'><span>{escape(specs[primary]['short_name'])}</span>"
                                f"<p>{escape(concise_text(brief['text']))}</p></div>", unsafe_allow_html=True)
                    if section["id"] == "financial" and raw_loader is not None:
                        render_policy_rates(specs, raw_loader, project_root)
                    with st.expander("Interpretation & transmission", expanded=False):
                        st.write(section["mechanism"])
                        st.caption(section["qualification"])
                        for key in chart_section["indicators"]:
                            st.markdown(f"**{specs[key]['name']}**")
                            render_reading(specs[key], metrics[key])
    st.caption("Five-year histories · indicator colors remain consistent · observations can differ by month")
    with st.expander("Signal definitions & comparison limits", expanded=False):
        st.write("Signals compare each indicator's configured transformation with its own rolling historical norm. They are not raw growth rates or theme composites. Dates can differ across indicators; inflation, borrowing costs and loan balances are contextual rather than good/bad scores.")
    with st.expander("Cycle anatomy · connect the channels", expanded=False):
        st.markdown("#### From intentions to activity")
        st.write("Orders and permits describe the pipeline. Production and real sales show how much activity is occurring. Firms can adjust hours before headcount, while employment and real income influence households' purchasing power. Inventories relative to sales help reveal whether production is matching demand. These relationships can overlap and do not follow a fixed timetable.")
        st.markdown("#### The financial feedback")
        st.write("Inflation and productivity shape cost pressure. Policy and financial conditions influence the price and availability of credit, which feeds back into housing, investment and spending. Market prices anticipate these developments but also respond to discount rates and risk appetite.")
        st.markdown("#### Read agreement and divergence")
        st.write("Compare the investment pipeline with current production; hours and claims with payrolls; income with sentiment and orders; and financial conditions with credit outstanding. Agreement adds breadth to the interpretation. Divergence identifies a relationship to investigate, rather than establishing a turning point by itself.")
        st.page_link("pages/05_Indicator.py", label="Open indicator research")


def load_comparisons(project_root):
    return yaml.safe_load((Path(project_root) / "config" / "research_comparisons.yaml").read_text(encoding="utf-8"))["comparisons"]


def comparison_chart(spec, metrics, column, start, end, shared_date, color):
    from src.analytics.interpretations import TRANSFORM_NAMES
    fig = go.Figure()
    if column in metrics:
        series = metrics[column].sort_index().loc[start:end]
        if series.notna().any():
            fig.add_trace(go.Scatter(x=series.index, y=series, mode="lines", name=spec["short_name"],
                                     connectgaps=False, line=dict(color=color, width=2),
                                     hovertemplate="%{x|%b %Y}<br>%{y:.2f}<extra>%{fullData.name}</extra>"))
    signal_view = column == "signal"
    if signal_view:
        unit = "Directional signal (σ)"
        fig.add_hrect(y0=-.25, y1=.25, line_width=0, fillcolor="#6D7275", opacity=.12, layer="below")
        fig.add_hline(y=0, line_dash="dot", line_color="rgba(199,214,213,.4)", line_width=1)
    else:
        transform = spec.get("signal_transform", "level")
        unit = TRANSFORM_NAMES.get(transform, "Economic measure").capitalize()
        unit += " (%)" if transform in {"yoy_pct", "return_6m", "growth_3m_ann"} else f" ({spec.get('units', 'units').replace('_', ' ')})"
    if shared_date is not None:
        fig.add_vline(x=shared_date, line_color="rgba(199,214,213,.35)", line_dash="dash", line_width=1)
    fig.update_layout(height=290, margin=dict(l=8, r=8, t=18, b=8), showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, Segoe UI, Arial", color="#C7D6D5", size=11),
                      hovermode="x", yaxis_title=unit)
    fig.update_xaxes(range=[start, end], showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(199,214,213,.08)", zeroline=False)
    if signal_view:
        fig.update_yaxes(range=[-3.2, 3.2], tickvals=[-3, -1.5, 0, 1.5, 3], ticksuffix="σ")
    return terminal_chart(fig)


def render_cross_indicator_research(project_root, registry, metric_loader):
    from src.analytics.comparisons import compare_indicators
    specs = {spec["id"]: spec for spec in registry}
    comparisons = load_comparisons(project_root)
    chapter_header(2, "CROSS-INDICATOR RESEARCH", "Connect the evidence.", "Where the channels reinforce each other—and where they diverge.")
    with st.container(key="comparison_workspace"):
        choose, lens = st.columns([1.15, 1], gap="large")
        with choose:
            label = st.selectbox("Relationship", [item["title"] for item in comparisons], key="research_relationship")
        with lens:
            view = st.radio("Chart lens", ["Standardized signal", "Economic measure"], horizontal=True, key="research_lens")
        config = next(item for item in comparisons if item["title"] == label)
        left_spec, right_spec = [specs[key] for key in config["indicators"]]
        left, right = [metric_loader(project_root, key) for key in config["indicators"]]
        reading = compare_indicators(left_spec, left, right_spec, right)
        st.markdown(f"<div class='comparison-question'>{escape(config['question'])}</div>", unsafe_allow_html=True)
        if reading["date"] is not None:
            st.caption(f"Shared reading · {reading['date'].strftime('%b %Y')} · All comparisons use the same month")
        dates = [m.index.max() for m in [left, right] if not m.empty]
        end = max(dates) if dates else pd.Timestamp.now()
        start = end - pd.DateOffset(years=5)
        column = "signal" if view == "Standardized signal" else "signal_input"
        panels = st.columns(2, gap="large")
        for number, (spec, metrics) in enumerate(zip([left_spec, right_spec], [left, right])):
            with panels[number]:
                st.markdown(f"**{spec['name']}**")
                if reading["evidence"]:
                    evidence = reading["evidence"][number]
                    st.markdown(f"<div class='comparison-value'>{evidence['signal']:+.2f}<span>σ</span></div>", unsafe_allow_html=True)
                    suffix = "%" if spec.get("signal_transform") in {"yoy_pct", "return_6m", "growth_3m_ann"} else ""
                    st.caption(f"{evidence['measure'].capitalize()}: {evidence['input']:+.2f}{suffix} at the shared month")
                    st.caption(f"Latest valid individual signal: {evidence['latest'].strftime('%b %Y')}")
                else:
                    st.caption("No shared standardized reading available")
                st.plotly_chart(comparison_chart(spec, metrics, column, start, end, reading["date"], indicator_color(spec["id"])),
                                use_container_width=True, config={"displayModeBar": False}, key=f"compare_{config['id']}_{number}")
        st.markdown(f"<div class='comparison-reading'><div class='research-eyebrow'>{escape(reading['headline'])}</div>"
                    f"<p>{escape(concise_text(reading['text']))}</p></div>", unsafe_allow_html=True)
        st.caption("Five-year history · dashed line = shared month · each indicator keeps the same color across views")
        with st.expander("Mechanism & interpretation limits", expanded=False):
            st.write(reading["text"])
            if reading["relationship"] == "divergence":
                st.write(config["divergence"])
            st.caption("Standardized charts share a scale; economic measures use their own units and scales. The numbers above show the shared-month signal and input in either lens.")
            st.write(config["mechanism"])
            st.write(config["qualification"])
            st.caption("Stronger/weaker compares each configured transformation with its own rolling norm; it does not mean positive/negative growth. Recent direction uses the actual transformed change over exactly three months, with the configured economic direction applied. No missing months are imputed by this comparison.")


def render_economic_tensions(project_root, metric_loader, composite_loader):
    from src.analytics.tensions import economic_tensions
    growth = composite_loader(project_root, "coincident")
    inflation = metric_loader(project_root, "headline_pce")
    financial = metric_loader(project_root, "financial_conditions")
    reading = economic_tensions(growth, inflation, financial, price_label="PCE", policy_reference=2.0)
    chapter_header(3, "ECONOMIC TENSIONS", "Growth, price pressure and the financing channel.", "Read the trade-offs behind policy transmission.")
    with st.container(key="economic_tensions"):
        st.markdown(f"<div class='tension-heading'>{escape(reading['headline'])}</div>", unsafe_allow_html=True)
        if reading["date"] is None:
            st.caption(reading["summary"])
            return
        st.caption(f"Shared evidence · {reading['date'].strftime('%b %Y')} · headline PCE is the inflation lens · target comparison uses 2%")
        columns = st.columns(3)
        for column, evidence in zip(columns, reading["evidence"]):
            column.metric(evidence["Channel"], evidence["Shared reading"])
            column.caption(evidence["Measure"])
            column.caption(f"3M change: {evidence['3M change']}")
        st.write(concise_text(reading["summary"]))
        st.caption(f"Inflation target comparison · {reading['evidence'][1]['Interpretation']}")
        st.markdown("**Policy transmission**")
        st.write(concise_text(reading["policy"]))
        st.caption("Conditional transmission scenario. Current policy actions and nominal borrowing benchmarks are shown in Financial conditions; NFCI improvement does not mean low loan rates.")
        with st.expander("Supporting evidence, mechanism & limits", expanded=False):
            st.dataframe(pd.DataFrame(reading["evidence"]), use_container_width=True, hide_index=True)
            st.write(reading["summary"])
            st.write(reading["policy"])
            if reading["history"]:
                fig = go.Figure()
                keys = {"growth": ("Coincident composite", "coincident_composite"),
                        "inflation": ("Headline PCE inflation · contextual", "headline_pce"),
                        "financial": ("Financial conditions · direction adjusted", "financial_conditions")}
                end = max(values.index.max() for values in reading["history"].values())
                start = end - pd.DateOffset(years=5)
                for key, values in reading["history"].items():
                    name, indicator_id = keys[key]
                    values = values.loc[start:]
                    fig.add_trace(go.Scatter(x=values.index, y=values, name=name, mode="lines", connectgaps=False,
                                             line=dict(color=indicator_color(indicator_id), width=2)))
                fig.add_hline(y=0, line_dash="dot", line_color="rgba(199,214,213,.4)")
                fig.add_vline(x=reading["date"], line_dash="dash", line_color="rgba(199,214,213,.35)")
                fig.update_layout(height=285, margin=dict(l=8,r=8,t=35,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="Inter, Segoe UI, Arial", color="#C7D6D5"), hovermode="x unified", legend=dict(orientation="h"))
                fig.update_xaxes(range=[start,end],showgrid=False)
                fig.update_yaxes(range=[-3.2,3.2],ticksuffix="σ",gridcolor="rgba(199,214,213,.08)")
                st.plotly_chart(terminal_chart(fig), use_container_width=True, config={"displayModeBar": False}, key="tensions_history")
                st.caption("Standardized history, not a combined score. Positive growth/financial signals are stronger or easier relative to their rolling norms; positive PCE inflation signals mean above-historical-norm price pressure, independently of the 2% goal.")
            for detail in reading["details"]:
                st.write(detail)
            st.markdown("[Monetary policy transmission · Federal Reserve](https://www.federalreserve.gov/aboutthefed/fedexplained/monetary-policy.htm) · [NFCI methodology · Chicago Fed](https://www.chicagofed.org/research/data/nfci/about)")
