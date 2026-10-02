"""Presentation-only Plotly treatment for Overview research charts."""
MONO_FONT = "Consolas, SFMono-Regular, Menlo, monospace"


def terminal_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Bahnschrift, Inter, Segoe UI, Arial", color="#DCE8ED", size=12),
        hoverlabel=dict(bgcolor="#0D1C26", bordercolor="#54D9EA", font=dict(family=MONO_FONT, color="#E8F4F8", size=12)),
        legend=dict(font=dict(family=MONO_FONT, color="#A1BAC7", size=11), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(tickfont=dict(family=MONO_FONT, color="#90AAB8", size=10), linecolor="rgba(84,217,234,.16)", showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(tickfont=dict(family=MONO_FONT, color="#90AAB8", size=10), gridcolor="rgba(122,168,189,.10)", zeroline=False, automargin=True)
    return fig
