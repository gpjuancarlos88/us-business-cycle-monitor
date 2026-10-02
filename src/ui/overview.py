"""Overview-only presentation for the personal economic research console."""
from html import escape
from pathlib import Path

import streamlit as st


def apply_overview_style():
    css = Path(__file__).with_name("overview.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def render_terminal_header(data_label, session_label):
    st.markdown(
        "<header class='command-hero' id='overview-top'>"
        "<div class='hero-topline'><span>UNITED STATES / MACROECONOMICS</span>"
        "<span>PERSONAL RESEARCH CONSOLE · V1</span></div>"
        "<div class='hero-core'>"
        "<div class='console-emblem' aria-hidden='true'><span></span><i></i></div>"
        "<div class='hero-eyebrow'>ECONOMIC INTELLIGENCE / OVERVIEW</div>"
        "<h1>U.S. BUSINESS CYCLE<span class='hero-title-line'>MONITOR</span></h1>"
        "<p class='hero-deck'>Read the cycle. Connect the evidence. Understand the transmission.</p>"
        "<div class='hero-telemetry'>"
        f"<div><span>LATEST OBSERVATION</span><strong>{escape(data_label)}</strong></div>"
        f"<div><span>VIEW REFRESHED · UTC</span><strong>{escape(session_label)}</strong></div>"
        "</div></div></header>",
        unsafe_allow_html=True,
    )


def render_chapter_navigation():
    chapters = [("01", "Economy"), ("02", "Relationships"), ("03", "Tensions"),
                ("04", "Cycle signals"), ("05", "History"), ("06", "Diagnostics")]
    with st.container(key="overview_index"):
        links = "".join(f"<a href='#chapter-{number}'><span>{number}</span>{label}</a>" for number, label in chapters)
        st.markdown(f"<nav class='chapter-index' aria-label='Overview chapters'>{links}</nav>", unsafe_allow_html=True)


def render_terminal_footer(cycle_count, context_count):
    st.markdown(
        "<footer class='console-footer'><div><span class='footer-mark'>US / BCM</span>"
        f"<span>{cycle_count} CYCLE INDICATORS + {context_count} CONTEXT SERIES</span></div>"
        "<a href='#overview-top'>RETURN TO OVERVIEW ↑</a></footer>",
        unsafe_allow_html=True,
    )
