from pathlib import Path
import pandas as pd
import pytest

from src.analytics.comparisons import compare_indicators
from src.ui.research import load_comparisons, comparison_chart
from src.indicators.registry import IndicatorRegistry


def spec(name, direction=1):
    return {'id':name, 'short_name':name, 'signal_transform':'yoy_pct', 'direction':direction, 'units':'index'}


def frame(score, start=1, end=2):
    dates=pd.date_range('2026-04-30',periods=4,freq='ME')
    return pd.DataFrame({'level':[100]*4,'signal':[score]*4,'signal_input':[start,start,end,end],'momentum':[2]*4},index=dates)


@pytest.mark.parametrize('left,right,relationship',[(.8,.5,'agreement'),(-.8,-.5,'agreement'),(.8,-.5,'divergence'),(.2,-.5,'mixed'),(.25,-.25,'mixed')])
def test_historical_positions(left,right,relationship):
    reading=compare_indicators(spec('A'),frame(left),spec('B'),frame(right))
    assert reading['relationship']==relationship
    assert reading['date']==pd.Timestamp('2026-07-31')


def test_latest_shared_month_and_exact_prior():
    left=frame(.8)
    right=frame(-.5).iloc[:-1]
    reading=compare_indicators(spec('A'),left,spec('B'),right)
    assert reading['date']==pd.Timestamp('2026-06-30')
    assert reading['evidence'][0]['latest']==pd.Timestamp('2026-07-31')
    assert 'newer individual reading' in reading['text']
    assert 'three-month directional comparison is unavailable' in reading['text']


def test_inverse_claims_and_actual_change_not_momentum():
    reading=compare_indicators(spec('Claims',-1),frame(.8,start=2,end=1),spec('Payrolls'),frame(.5,start=2,end=1))
    assert reading['relationship']=='agreement'
    assert reading['evidence'][0]['trend']=='strengthening'
    assert reading['evidence'][1]['trend']=='weakening'
    assert 'recent directions differ' in reading['text']


def test_unchanged_and_same_direction():
    reading=compare_indicators(spec('A'),frame(.8,1,1),spec('B'),frame(.6,2,2))
    assert 'Both underlying directional measures are unchanged' in reading['text']


def test_no_shared_or_nonfinite_signals():
    left=frame(.8)
    right=frame(.5)
    right.index=right.index+pd.offsets.MonthEnd(12)
    assert compare_indicators(spec('A'),left,spec('B'),right)['date'] is None
    assert compare_indicators(spec('A'),pd.DataFrame(),spec('B'),right)['date'] is None
    assert compare_indicators(spec('A'),frame(float('inf')),spec('B'),frame(.5))['date'] is None


def test_missing_latest_row_uses_shared_valid_month():
    left=frame(.8)
    left.loc[left.index[-1],'signal']=float('nan')
    reading=compare_indicators(spec('A'),left,spec('B'),frame(.5))
    assert reading['date']==pd.Timestamp('2026-06-30')


def test_missing_calendar_month_does_not_use_third_previous_row():
    left=frame(.8).drop(pd.Timestamp('2026-04-30'))
    reading=compare_indicators(spec('A'),left,spec('B'),frame(.5))
    assert reading['evidence'][0]['trend']=='unavailable'


def test_comparison_config_and_chart_alignment():
    root=Path(__file__).resolve().parents[1]
    registry={s['id']:s for s in IndicatorRegistry(root/'config/indicators.yaml').all()}
    comparisons=load_comparisons(root)
    assert len(comparisons)==4
    assert len({c['id'] for c in comparisons})==4
    for comparison in comparisons:
        assert len(comparison['indicators'])==2
        assert all(registry[key]['direction'] in [-1,1] for key in comparison['indicators'])
    start,end=pd.Timestamp('2021-07-31'),pd.Timestamp('2026-07-31')
    signal=comparison_chart(spec('A'),frame(.8),'signal',start,end,end,'#C7D6D5')
    economic=comparison_chart(spec('B'),frame(.8),'signal_input',start,end,end,'#8FAABF')
    assert signal.layout.xaxis.range==economic.layout.xaxis.range
    assert signal.layout.yaxis.range==(-3.2,3.2)
    assert economic.layout.yaxis.range is None
    assert '(%)' in economic.layout.yaxis.title.text
    assert not signal.data[0].connectgaps
