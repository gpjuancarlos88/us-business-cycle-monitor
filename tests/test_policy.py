from pathlib import Path
import pandas as pd
from src.analytics.policy import policy_snapshot, inflation_snapshot
from src.analytics.tensions import economic_tensions
from src.analytics.interpretations import indicator_reading
from src.indicators.registry import IndicatorRegistry


def raw(values):
    return pd.DataFrame({'observation_date':pd.date_range('2026-09-15',periods=len(values),freq='D'),'value':values})


def test_policy_daily_hike_not_monthly_average():
    result=policy_snapshot({'fed_target_lower':raw([3.5,3.5,3.75,3.75]),'fed_target_upper':raw([3.75,3.75,4,4]),'sofr':raw([3.6,3.6,3.9,3.9])})
    assert result['range']['lower']==3.75
    assert result['range']['upper']==4
    assert result['change']['lower_bps']==25
    assert result['change']['action']=='Hike'
    assert result['change']['date']==pd.Timestamp('2026-09-17')
    assert result['rates']['sofr']['value']==3.9


def test_cut_reshape_single_row_and_missing_bounds():
    result=policy_snapshot({'fed_target_lower':raw([4,3.75]),'fed_target_upper':raw([4.25,4])})
    assert result['change']['action']=='Cut'
    result=policy_snapshot({'fed_target_lower':raw([4,4]),'fed_target_upper':raw([4.25,4.5])})
    assert result['change']['action']=='Range reshaped'
    assert policy_snapshot({'fed_target_lower':raw([4]),'fed_target_upper':raw([4.25])})['change'] is None
    assert policy_snapshot({'fed_target_lower':raw([4])})['range'] is None
    assert policy_snapshot({'fed_target_lower':raw([5]),'fed_target_upper':raw([4])})['range'] is None


def test_above_target_inflation_even_if_historical_zscore_zero():
    dates=pd.date_range('2026-04-30',periods=4,freq='ME')
    growth=pd.DataFrame({'score':[.8,.7,.6,.4]},index=dates)
    inflation=pd.DataFrame({'signal':[0]*4,'signal_input':[3.7,3.5,3.4,3.4]},index=dates)
    financial=pd.DataFrame({'signal':[.6]*4,'level':[-.1,-.2,-.3,-.4]},index=dates)
    result=economic_tensions(growth,inflation,financial,price_label='PCE',policy_reference=2)
    assert result['persistent']
    assert 'pressure persists' in result['headline']
    assert 'above the 2%' in result['summary']
    assert '1.40' in result['evidence'][1]['Interpretation']
    assert 'does not establish low benchmark rates' in result['policy']


def test_context_universe_does_not_expand_original_composites():
    registry=IndicatorRegistry(Path(__file__).resolve().parents[1]/'config/indicators.yaml')
    assert len(registry.by_category('leading'))==10
    assert len(registry.by_category('coincident'))==4
    assert len(registry.by_category('lagging'))==7
    assert len(registry.by_category('context'))==9
    assert all(s['direction']==0 for s in registry.by_category('context'))


def test_inflation_snapshot_absolute_values_without_zscore():
    keys=['headline_pce','core_pce','headline_cpi','core_cpi']
    specs={k:{'short_name':k} for k in keys}
    m=pd.DataFrame({'level':[100],'yoy_pct':[3.4],'mom_pct':[.3],'growth_3m_ann':[2.7],'signal':[0]},index=[pd.Timestamp('2026-08-31')])
    rows=inflation_snapshot(specs,{k:m for k in keys})
    assert abs(rows[0]['gap']-1.4)<1e-10
    assert rows[0]['mom']==.3
    assert rows[2]['gap'] is None
    reading=indicator_reading({'id':'headline_pce','signal_transform':'yoy_pct','direction':0,'policy_reference':2},m.assign(signal_input=3.4))
    assert 'above the 2%' in reading['text']
    assert 'near its rolling historical norm' in reading['text']
