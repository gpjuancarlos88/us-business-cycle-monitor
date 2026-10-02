"""Inflation and borrowing-cost evidence in the existing theme panels."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.analytics.policy import inflation_snapshot, policy_snapshot, INFLATION_IDS, RATE_IDS
from src.charts.palette import indicator_color
from src.charts.terminal import terminal_chart


def _chart_layout(fig, title):
    fig.update_layout(height=240, margin=dict(l=8,r=8,t=35,b=8), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Inter, Segoe UI, Arial',color='#C7D6D5',size=10), hovermode='x unified', legend=dict(orientation='h',y=1.02,yanchor='bottom'), yaxis_title=title)
    fig.update_xaxes(showgrid=False,tickformat='%Y',dtick='M12')
    fig.update_yaxes(gridcolor='rgba(199,214,213,.08)')
    return terminal_chart(fig)


def render_inflation(specs, metrics):
    rows = inflation_snapshot(specs, metrics)
    st.caption('Absolute inflation rates · historical average is not the policy goal')
    for offset in range(0, 4, 2):
        columns = st.columns(2)
        for column, row in zip(columns, rows[offset:offset+2]):
            column.metric(row['name']+' · YoY', f"{row['yoy']:.2f}%" if row['yoy'] is not None else 'N/A')
            column.caption(row['date'].strftime('%b %Y') if row['date'] is not None else 'No data')
    headline = rows[0]
    if headline['gap'] is not None:
        state = 'above' if headline['gap'] > 1e-10 else 'below' if headline['gap'] < -1e-10 else 'at'
        st.markdown(f"**Headline PCE is {state} the Fed’s 2% longer-run goal** · gap {headline['gap']:+.2f} percentage points.")
    else:
        st.caption('Headline PCE target comparison is unavailable; a services inflation Z-score cannot substitute for it.')
    fig = go.Figure()
    dates = [metrics[key].index.max() for key in INFLATION_IDS if not metrics[key].empty]
    if dates:
        end = max(dates); start = end-pd.DateOffset(years=5)
        for key in INFLATION_IDS:
            frame = metrics[key]
            if 'yoy_pct' in frame:
                values = frame['yoy_pct'].loc[start:]
                fig.add_trace(go.Scatter(x=values.index,y=values,name=specs[key]['short_name'],mode='lines',connectgaps=False,line=dict(color=indicator_color(key),width=1.8)))
        fig.add_hline(y=2,line_dash='dot',line_color='#C7D6D5')
        fig.update_xaxes(range=[start,end])
        st.plotly_chart(_chart_layout(fig,'YoY inflation (%)'),use_container_width=True,config={'displayModeBar':False},key='absolute_inflation_history')
    st.caption('Dotted line: 2% headline PCE goal; a reference for core PCE, not a CPI target. Core excludes food and energy.')
    with st.expander('Inflation momentum & definitions',expanded=False):
        display = []
        for row in rows:
            display.append({'Measure':row['name'],'Month':row['date'].strftime('%b %Y') if row['date'] is not None else 'Missing',
                            'YoY (%)':row['yoy'],'MoM (%)':row['mom'],'3M annualized (%)':row['annualized_3m'],
                            'PCE gap to 2% reference (pp)':row['gap']})
        st.dataframe(pd.DataFrame(display),use_container_width=True,hide_index=True)
        st.write('Headline PCE is the measure for the Fed’s longer-run 2% goal. Core PCE helps assess underlying pressure; CPI measures a different price basket. A rate above its policy reference can be falling, and a near-average historical Z-score can still correspond to above-target inflation.')
        st.caption('Calculated from seasonally adjusted price indices. CPI YoY can differ slightly from BLS published unadjusted YoY rates. Monthly and annualized rates are distinct; this view uses each series’ latest observation and labels differing months.')
        st.markdown('[Fed inflation goal](https://www.federalreserve.gov/faqs/economy_14400.htm) · [BEA PCE methodology](https://www.bea.gov/data/personal-consumption-expenditures-price-index)')


def render_policy_rates(specs, raw_loader, project_root):
    snapshot = policy_snapshot({key:raw_loader(project_root,key) for key in RATE_IDS})
    st.markdown('**Policy rate & nominal borrowing benchmarks**')
    target = snapshot['range']
    if target:
        st.metric('Fed target range',f"{target['lower']:.2f}–{target['upper']:.2f}%")
        st.caption(f"Range observed {target['date'].strftime('%d %b %Y')}")
        change = snapshot['change']
        if change:
            amount = f"{change['lower_bps']:+.0f} bp" if change['action']!='Range reshaped' else f"lower {change['lower_bps']:+.0f} bp / upper {change['upper_bps']:+.0f} bp"
            st.markdown(f"**Last observed change: {change['action']} · {amount}**")
            st.caption(f"First observed on {change['date'].strftime('%d %b %Y')} · not the FOMC announcement date")
        else:
            st.caption('No earlier range change available in the loaded history.')
    else:
        st.caption('The policy target range is unavailable. NFCI cannot substitute for the Fed policy rate.')
    columns=st.columns(3)
    for column,key in zip(columns,['effective_fed_funds','sofr','treasury_10y']):
        rate=snapshot['rates'][key]
        column.metric(specs[key]['short_name'],f"{rate['value']:.2f}%" if rate else 'N/A')
        column.caption(rate['date'].strftime('%d %b %Y') if rate else 'Missing')
    st.caption('Latest daily observations. Broad conditions improving does not establish low benchmark rates or cheap borrowing.')
    st.write('Floating-rate borrowing follows the loan’s contractual benchmark plus its spread, floors and fees. Improving NFCI can coexist with high base rates; it does not establish that debt service has fallen.')
    with st.expander('Borrowing-cost transmission & rate history',expanded=False):
        st.write('A floating-rate loan depends on its contractual benchmark convention plus the borrower’s credit spread, floors and fees. Overnight SOFR shown here is a reference; a contract may use term SOFR or compounded averages. The 10-year Treasury yield is a long-term nominal benchmark, not a floating-loan coupon.')
        st.write('NFCI summarizes funding, leverage and market conditions. It can improve through spreads or asset prices while nominal base rates remain high. A rate hike describes policy action; inflation can still be decelerating but remain above target. Any discussion of easing as a demand cushion is a conditional scenario, not a claim that easing has occurred.')
        fig=go.Figure(); dates=[s.index.max() for s in snapshot['history'].values() if not s.empty]
        if dates:
            end=max(dates); start=end-pd.DateOffset(years=5)
            for key,values in snapshot['history'].items():
                values=values.loc[start:]
                if not values.empty:
                    fig.add_trace(go.Scatter(x=values.index,y=values,name=specs[key]['short_name'],mode='lines',connectgaps=False,line=dict(color=indicator_color(key),width=1.6)))
            fig.update_xaxes(range=[start,end])
            st.plotly_chart(_chart_layout(fig,'Nominal rate (%)'),use_container_width=True,config={'displayModeBar':False},key='nominal_rates_history')
        st.markdown('[FOMC decisions](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) · [SOFR source: New York Fed via FRED](https://fred.stlouisfed.org/series/SOFR) · [10-year Treasury source](https://fred.stlouisfed.org/series/DGS10)')
