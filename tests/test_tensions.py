import pandas as pd
import pytest

from src.analytics.tensions import economic_tensions
from src.charts.palette import INDICATOR_COLORS, indicator_color
from src.charts.timeseries import line_chart
from src.indicators.registry import IndicatorRegistry
from src.ui.research import theme_chart, comparison_chart, concise_text
from pathlib import Path


def data(growth_end=.1, inflation_end=3, inflation_score=.8, finance_end=.3):
    dates=pd.date_range('2026-04-30',periods=4,freq='ME')
    growth=pd.DataFrame({'score':[.8,.6,.4,growth_end],'coverage':[4]*4},index=dates)
    inflation=pd.DataFrame({'signal':[inflation_score]*4,'signal_input':[4,3.8,3.5,inflation_end]},index=dates)
    financial=pd.DataFrame({'signal':[-.4]*4,'level':[-.2,-.1,.1,finance_end]},index=dates)
    return growth,inflation,financial


def test_weakening_activity_persistent_services_and_tightening():
    reading=economic_tensions(*data())
    assert reading['persistent']
    assert 'pressure persists' in reading['headline']
    assert 'tightened' in reading['summary']
    assert 'restraint on demand' in reading['policy']
    assert reading['evidence'][1]['Shared reading']=='+3.00%'
    assert reading['evidence'][1]['3M change']=='-1.000 pp'
    assert 'not GDP growth' in reading['evidence'][0]['Interpretation']


def test_above_normal_once_is_not_persistent():
    growth,inflation,financial=data()
    inflation.loc[inflation.index[-2],'signal']=.1
    reading=economic_tensions(growth,inflation,financial)
    assert not reading['persistent']
    assert 'pressure elevated' in reading['headline']


def test_missing_persistence_month_is_not_filled():
    growth,inflation,financial=data()
    inflation.loc[inflation.index[-2],'signal_input']=float('nan')
    reading=economic_tensions(growth,inflation,financial)
    assert not reading['persistent']
    assert any('consecutive monthly readings' in d for d in reading['details'])


@pytest.mark.parametrize('growth,score,headline',[(.1,-.5,'softening · services disinflation'),(1.1,.8,'strengthening · services pressure elevated'),(1.1,-.5,'strengthening · services disinflation')])
def test_other_tension_cases(growth,score,headline):
    reading=economic_tensions(*data(growth_end=growth,inflation_score=score))
    assert headline in reading['headline']


def test_easing_is_distinct_from_tight_level():
    growth,inflation,financial=data()
    financial['level']=[.8,.7,.5,.3]
    reading=economic_tensions(growth,inflation,financial)
    assert 'eased' in reading['summary']
    assert 'does not establish low benchmark rates' in reading['policy']


def test_shared_month_not_individual_latest():
    growth,inflation,financial=data()
    reading=economic_tensions(growth,inflation.iloc[:-1],financial)
    assert reading['date']==pd.Timestamp('2026-06-30')
    assert reading['incomplete']
    assert 'direction incomplete' in reading['headline']
    assert any('Newer individual' in d for d in reading['details'])


def test_missing_three_month_baseline_withholds_case():
    growth,inflation,financial=data()
    reading=economic_tensions(growth.iloc[1:],inflation,financial)
    assert reading['incomplete']
    assert 'withheld' in reading['summary']


def test_unavailable_and_nonfinite_data():
    growth,inflation,financial=data()
    assert economic_tensions(pd.DataFrame(),inflation,financial)['date'] is None
    inflation['signal']=float('inf')
    assert economic_tensions(growth,inflation,financial)['date'] is None


def test_no_persistent_positive_pressure_under_deflation():
    growth,inflation,financial=data(inflation_end=-1)
    inflation['signal_input']=-1
    reading=economic_tensions(growth,inflation,financial)
    assert not reading['persistent']
    assert 'No clear' in reading['headline']


def test_stable_indicator_color_across_charts():
    root=Path(__file__).resolve().parents[1]
    specs={s['id']:s for s in IndicatorRegistry(root/'config/indicators.yaml').all()}
    assert set(specs)<=set(INDICATOR_COLORS)
    dates=pd.date_range('2026-04-30',periods=4,freq='ME')
    metrics=pd.DataFrame({'signal':[.8]*4,'signal_input':[1,2,3,4]},index=dates)
    key='industrial_production'
    theme=theme_chart({'indicators':[key]},specs,{key:metrics})
    pair=comparison_chart(specs[key],metrics,'signal',dates[0],dates[-1],dates[-1],indicator_color(key))
    individual=line_chart(metrics['signal'],'Industrial Production',indicator_id=key)
    assert theme.data[0].line.color==pair.data[0].line.color==individual.data[0].line.color


def test_concise_copy_retains_numeric_value_and_direction():
    full='The year-over-year growth rate is +1.42%. Its growth rate is above its norm. The directional measure has weakened versus three months earlier. Its historical position and recent direction differ.'
    brief=concise_text(full)
    assert '+1.42%' in brief
    assert 'weakened versus three months' in brief
    assert 'historical position' not in brief
